import os
import glob
import time
import queue
import threading
from pathlib import Path
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

from app.core.llm_factory import get_llm
from app.core.embeddings import get_embeddings
from app.core.prompts import get_qa_prompt
from services.file_loader import load_documents
from services.chunking import split_documents


class HemasPharmaComplyAI:
    def __init__(self, config):
        self.config = config

        self.data_dir = Path(config["paths"]["data_dir"]).resolve()
        self.vector_store_path = Path(config["paths"]["vector_store"]).resolve()

        self.query_count = 0
        self.total_tokens = 0
        self.start_time = time.time()

        self.llm = get_llm(config)
        self.embeddings = get_embeddings(config)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        self.vector_store = None
        self.qa_chain = None
        self.processed_files = set()
        self.is_ready = False
        self.last_load_error = None

        if config.get("auto_load", True):
            self.is_ready = self.auto_load_gazettes()

    def auto_load_gazettes(self):
        self.last_load_error = None
        st.info(f"🔍 Scanning {self.data_dir} for NMRA gazettes...")
        
        file_patterns = [
            str(self.data_dir / "**/*.pdf"),
            str(self.data_dir / "**/*.txt"),
            str(self.data_dir / "**/*.docx"),
            str(self.data_dir / "**/*.doc"),
            str(self.data_dir / "**/*.png"),
            str(self.data_dir / "**/*.jpg"),
            str(self.data_dir / "**/*.jpeg")
        ]
        
        all_files = []
        for pattern in file_patterns:
            all_files.extend(glob.glob(pattern, recursive=True))

        all_files = sorted({str(Path(file_path).resolve()) for file_path in all_files})
            
        if not all_files:
            self.is_ready = False
            self.last_load_error = f"No gazette files found in {self.data_dir}"
            st.warning(f"📭 No gazette files found in {self.data_dir}")
            return False
            
        st.success(f"📁 Found {len(all_files)} gazette file(s)")
        
        missing_files = self._get_missing_files(all_files)
        
        if not missing_files and self._load_existing_vector_store():
            st.info("✅ Loading existing vector store (Up to date)...")
            self.vector_store = Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )
            self.create_chain()
            self.is_ready = True
            return True
        else:
            if not missing_files:
                st.warning("âš ï¸ Existing vector store is empty or unreadable. Rebuilding from gazette files...")
                missing_files = all_files
            if self.vector_store_path.exists() and any(self.vector_store_path.iterdir()):
                st.info(f"🔄 Found {len(missing_files)} new file(s). Updating database...")
                self.vector_store = Chroma(
                    persist_directory=str(self.vector_store_path),
                    embedding_function=self.embeddings
                )
            else:
                st.info("🔄 Initializing document database...")
                
            return self.process_files(missing_files)

    def _get_missing_files(self, current_files):
        """
        Identifies which files from the current list are not yet in the vector store.
        """
        if not self.vector_store_path.exists() or not any(self.vector_store_path.iterdir()):
            return current_files
            
        try:
            temp_store = Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )
            if not self._has_indexed_documents(temp_store):
                return current_files

            existing_data = temp_store._collection.get(include=["metadatas"])
            existing_sources = set()
            for metadata in existing_data.get("metadatas") or []:
                if not metadata:
                    continue
                existing_sources.update(self._build_file_keys(metadata.get("source", "")))
                existing_sources.update(self._build_file_keys(metadata.get("file_path", "")))
            missing = []
            for f in current_files:
                if not (self._build_file_keys(f) & existing_sources):
                    missing.append(f)
            return missing
        except Exception:
            return current_files

    def process_files(self, file_paths):
        try:
            if not file_paths and self._has_indexed_documents():
                self.create_chain()
                self.is_ready = True
                return True

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📄 Loading documents...")
            documents = load_documents(file_paths)
            progress_bar.progress(0.4)
            
            if not documents:
                self.is_ready = False
                self.last_load_error = "No readable content could be extracted from the gazette files."
                return False
                
            status_text.text("✂️ Splitting into chunks...")
            chunks = split_documents(documents, self.config)
            progress_bar.progress(0.7)
            
            status_text.text("💾 Updating vector database...")
            if self.vector_store is not None:
                self.vector_store.add_documents(chunks)
            else:
                self.vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=str(self.vector_store_path)
                )

            self._persist_vector_store()
            if not self._has_indexed_documents():
                raise RuntimeError("Vector store did not persist any indexed chunks.")
            
            self.create_chain()
            progress_bar.progress(1.0)
            
            status_text.text("✅ Processing complete!")
            self.processed_files.update(file_paths)
            self.is_ready = True
            
            st.success(f"✅ Successfully processed {len(documents)} document chunks")
            return True
        except Exception as e:
            self.is_ready = False
            self.last_load_error = str(e)
            st.error(f"❌ Error processing files: {e}")
            return False

    def create_chain(self):
        prompt = PromptTemplate(
            template=get_qa_prompt(),
            input_variables=["context", "question"]
        )
        
        # EXPLICIT CONTEXT LABELLING: This ensures the LLM sees the source/page for every chunk!
        document_prompt = PromptTemplate(
            input_variables=["page_content", "source", "page"],
            template="[DOCUMENT: {source}, PAGE: {page}]\n{page_content}\n"
        )
        
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.config["retrieval"]["top_k"]}
        )
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={
                "prompt": prompt,
                "document_prompt": document_prompt
            },
            return_source_documents=True,
            verbose=False
        )

    def query(self, question):
        if not self.qa_chain:
            return {"error": "Gazette documents not loaded."}
        
        start_time = time.time()
        try:
            result = self.qa_chain.invoke({"question": question})
            answer = result.get('answer', '')
            
            self.query_count += 1
            self.total_tokens += len(question) + len(answer)
            query_time = time.time() - start_time
            
            show_sources = self._should_show_sources(question, answer)
            suggestions = self._generate_followup_questions(answer) if show_sources else []
            sources = self._extract_sources(result) if show_sources else []
            
            return {
                "answer": answer,
                "suggestions": suggestions,
                "sources": sources,
                "query_time": f"{query_time:.2f}s",
                "query_count": self.query_count
            }
        except Exception as e:
            return {"error": str(e)}

    def stream_query(self, question):
        if not self.qa_chain:
            yield {"error": "Gazette documents not loaded."}
            return
            
        start_time = time.time()
        token_queue = queue.Queue()
        
        class QueueCallback(BaseCallbackHandler):
            def __init__(self, q):
                self.q = q
            def on_llm_new_token(self, token: str, **kwargs) -> None:
                self.q.put(token)
            def on_llm_end(self, *args, **kwargs) -> None:
                pass
            def on_llm_error(self, error: Exception, **kwargs) -> None:
                self.q.put(error)
                
        def run_chain():
            try:
                result = self.qa_chain.invoke(
                    {"question": question},
                    config={"callbacks": [QueueCallback(token_queue)]}
                )
                token_queue.put(result)
            except Exception as e:
                token_queue.put(e)
                
        thread = threading.Thread(target=run_chain)
        thread.start()
        
        answer_accumulated = ""
        while True:
            try:
                item = token_queue.get(timeout=120)
                if isinstance(item, str):
                    answer_accumulated += item
                    yield item
                elif isinstance(item, dict) and "answer" in item:
                    query_time = time.time() - start_time
                    self.query_count += 1
                    self.total_tokens += len(question) + len(answer_accumulated)
                    
                    show_sources = self._should_show_sources(question, item['answer'])
                    suggestions = self._generate_followup_questions(item['answer']) if show_sources else []
                    sources = self._extract_sources(item) if show_sources else []
                            
                    yield {
                        "type": "final",
                        "answer": item['answer'],
                        "suggestions": suggestions,
                        "sources": sources,
                        "query_time": f"{query_time:.2f}s",
                        "query_count": self.query_count
                    }
                    break
                elif isinstance(item, Exception):
                    yield {"error": str(item)}
                    break
            except queue.Empty:
                yield {"error": "Timeout waiting for response"}
                break

    def _generate_followup_questions(self, answer):
        try:
            prompt = f"Based on the answer below, suggest 3 short, relevant follow-up questions.\nAnswer: {answer}\nFormat:\n- Provide ONLY 3 questions\n- Separate by newlines\n- No numbering, Keep concise"
            if hasattr(self.llm, "invoke"):
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
            else:
                response = self.llm(prompt)
                content = str(response)
                
            questions = [q.strip() for q in content.split('\n') if q.strip()]
            final_questions = []
            for q in questions:
                clean_q = q.lstrip('1234567890.- ').strip()
                if clean_q and '?' in clean_q:
                    final_questions.append(clean_q)
            return final_questions[:3]
        except:
            return []

    def _extract_sources(self, result):
        answer = result.get('answer', '')
        source_docs = result.get('source_documents', [])
        sources = []
        seen = set()

        # Helper to calculate basic keyword overlap (simple relevance check)
        def get_relevance_score(text, ref_text):
            text_words = set(text.lower().split())
            ref_words = set(ref_text.lower().split())
            # Basic score: how many words from the source are in the answer?
            if not text_words: return 0
            overlap = text_words.intersection(ref_words)
            return len(overlap) / len(text_words)

        # First pass: Look for explicit citations matching (Document, Page)
        for doc in source_docs:
            doc_name = doc.metadata.get('source', 'Unknown')
            page = str(doc.metadata.get('page', ''))
            doc_stem = Path(doc_name).stem.lower()
            
            # Check if both doc name and page are in the answer
            citation_present = (doc_stem in answer.lower()) and (f"page {page}" in answer.lower() or f"p.{page}" in answer.lower() or f"p {page}" in answer.lower())
            
            if citation_present:
                excerpt = doc.page_content[:400].replace('\n', ' ').strip()
                key = (doc_name, page, excerpt[:100])
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "document": doc_name,
                        "file_path": doc.metadata.get('file_path', ''),
                        "page": page,
                        "excerpt": f"{excerpt}..." if excerpt else "No excerpt available."
                    })

        # Second pass fallback: If no explicit citations matched, perform RELEVANCE SCORING
        # this helps when the LLM misses the page number but uses the doc.
        if not sources:
            scored_sources = []
            for doc in source_docs:
                doc_name = doc.metadata.get('source', 'Unknown')
                doc_stem = Path(doc_name).stem.lower()
                
                # Check if the document name is mentioned and if it has high keyword overlap
                if doc_stem in answer.lower():
                    # Check text overlap: is the content of this chunk actually in the answer?
                    rel_score = get_relevance_score(answer, doc.page_content)
                    
                    # Threshold: if at least some significant keywords overlap
                    if rel_score > 0.05: # Minimal threshold
                        page = str(doc.metadata.get('page', 'N/A'))
                        excerpt = doc.page_content[:400].replace('\n', ' ').strip()
                        key = (doc_name, page, excerpt[:100])
                        if key not in seen:
                            seen.add(key)
                            scored_sources.append({
                                "score": rel_score,
                                "document": doc_name,
                                "file_path": doc.metadata.get('file_path', ''),
                                "page": page,
                                "excerpt": f"{excerpt}..."
                            })
            
            # Sort by score and take the best ones (only if they are actually good)
            scored_sources.sort(key=lambda x: x["score"], reverse=True)
            # Only include sources that significantly relate (top 2 if no explicit citing)
            for s in scored_sources[:2]:
                sources.append({
                    "document": s["document"],
                    "file_path": s["file_path"],
                    "page": s["page"],
                    "excerpt": s["excerpt"]
                })

        # Final fallback: If still nothing, and not a refusal, show top 1
        if not sources and source_docs and "i cannot find" not in answer.lower():
            doc = source_docs[0]
            sources.append({
                "document": doc.metadata.get('source', 'Unknown'),
                "file_path": doc.metadata.get('file_path', ''),
                "page": doc.metadata.get('page', 'N/A'),
                "excerpt": doc.page_content[:400].replace('\n', ' ').strip() + "..."
            })

        return sources

    def _load_existing_vector_store(self):
        self.vector_store = Chroma(
            persist_directory=str(self.vector_store_path),
            embedding_function=self.embeddings
        )
        return self._has_indexed_documents(self.vector_store)

    def _has_indexed_documents(self, store=None):
        active_store = store or self.vector_store
        if active_store is None:
            return False

        try:
            return active_store._collection.count() > 0
        except Exception:
            try:
                existing_data = active_store._collection.get(include=[])
                return bool(existing_data.get("ids"))
            except Exception:
                return False

    def _persist_vector_store(self):
        if self.vector_store is None:
            return

        persist = getattr(self.vector_store, "persist", None)
        if callable(persist):
            persist()

    def _build_file_keys(self, value):
        if not value:
            return set()

        raw_path = Path(str(value))
        keys = {raw_path.name.lower(), str(raw_path).lower()}

        try:
            keys.add(str(raw_path.resolve()).lower())
        except Exception:
            pass

        return keys

    def _should_show_sources(self, question, answer):
        normalized_question = (question or "").strip().lower()
        normalized_answer = (answer or "").strip().lower()

        greeting_inputs = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
        refusal_markers = (
            "i can only answer questions about nmra pharmaceutical price regulations",
            "i cannot find information about",
            "hello. i am hemas pharmacomply ai."
        )

        if normalized_question in greeting_inputs:
            return False

        return not any(marker in normalized_answer for marker in refusal_markers)
