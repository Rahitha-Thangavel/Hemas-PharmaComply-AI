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

        self.data_dir = Path(config["paths"]["data_dir"])
        self.vector_store_path = Path(config["paths"]["vector_store"])

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

        if config.get("auto_load", True):
            self.auto_load_gazettes()

    def auto_load_gazettes(self):
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
            
        if not all_files:
            st.warning(f"📭 No gazette files found in {self.data_dir}")
            return False
            
        st.success(f"📁 Found {len(all_files)} gazette file(s)")
        
        if self._check_existing_vector_store(all_files):
            st.info("✅ Loading existing vector store...")
            self.vector_store = Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )
            self.create_chain()
            return True
        else:
            st.info("🔄 Processing gazette files...")
            return self.process_files(all_files)

    def _check_existing_vector_store(self, current_files):
        if not self.vector_store_path.exists() or not any(self.vector_store_path.iterdir()):
            return False
        try:
            temp_store = Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )
            existing_data = temp_store._collection.get()
            if not existing_data['metadatas']:
                return False
            existing_sources = set([m.get('source', '') for m in existing_data['metadatas']])
            current_sources = set([Path(f).name for f in current_files])
            return current_sources.issubset(existing_sources)
        except:
            return False

    def process_files(self, file_paths):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📄 Loading documents...")
            documents = load_documents(file_paths)
            progress_bar.progress(0.4)
            
            if not documents:
                return False
                
            status_text.text("✂️ Splitting into chunks...")
            chunks = split_documents(documents, self.config)
            progress_bar.progress(0.7)
            
            status_text.text("💾 Creating vector database...")
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.vector_store_path)
            )
            self.create_chain()
            progress_bar.progress(1.0)
            
            status_text.text("✅ Processing complete!")
            self.processed_files.update(file_paths)
            
            st.success(f"✅ Successfully processed {len(documents)} document chunks")
            return True
        except Exception as e:
            st.error(f"❌ Error processing files: {e}")
            return False

    def create_chain(self):
        prompt = PromptTemplate(
            template=get_qa_prompt(),
            input_variables=["context", "question"]
        )
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.config["retrieval"]["top_k"]}
        )
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": prompt},
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
        sources = []
        seen = set()

        for doc in result.get('source_documents', []):
            document = doc.metadata.get('source', 'Unknown')
            category = doc.metadata.get('category', 'Regulatory')
            year = doc.metadata.get('year', '')
            page = doc.metadata.get('page', 'N/A')
            excerpt = doc.page_content[:200].strip()
            key = (document, page, excerpt)

            if key in seen:
                continue

            seen.add(key)
            
            # Format source name to include category and year
            source_label = f"{document} [{category}]"
            if year and year != 0:
                source_label = f"{document} [{category} - {year}]"

            sources.append({
                "document": source_label,
                "page": page,
                "excerpt": f"{excerpt}..." if excerpt else "No excerpt available."
            })

        return sources

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
