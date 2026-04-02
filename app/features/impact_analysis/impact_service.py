import pandas as pd
import os
import re
from datetime import datetime

class ImpactService:
    def __init__(self, chatbot, products_csv_path):
        self.chatbot = chatbot
        self.products_csv_path = products_csv_path
        self.products_df = self._load_products()
        self.last_raw_response = ""
        self.last_context = ""
        self.last_raw_findings = []

    def _load_products(self):
        """Loads and cleans the internal products catalog"""
        if os.path.exists(self.products_csv_path):
            try:
                df = pd.read_csv(self.products_csv_path)
                df['current_mrp'] = pd.to_numeric(df['current_mrp'], errors='coerce')
                return df
            except Exception as e:
                print(f"Error loading products: {e}")
        return pd.DataFrame(columns=["product_brand", "active_ingredient", "current_mrp", "category", "status"])

    def predict_impact(self, target_filename=None):
        """
        Analysis Engine with SOURCE-SPECIFIC FILTERING (Fixes retrieval misses)
        """
        # --- ENHANCED RETRIEVAL ---
        # If the user uploaded a specific file, we search ONLY that file for 100% accuracy
        context_chunks = []
        if self.chatbot.vector_store:
            search_query = "Price Table Generic Strength MRP Maximum Retail Price Schedule"
            
            search_kwargs = {"k": 60} # Increased to 60 chunks to cover potential multi-page tables
            if target_filename:
                # Filter specifically for the uploaded gazette
                search_kwargs["filter"] = {"source": target_filename}
            
            docs = self.chatbot.vector_store.similarity_search(search_query, **search_kwargs)
            context_chunks = [f"[FILE: {d.metadata.get('source')}, PAGE: {d.metadata.get('page')}] {d.page_content}" for d in docs]
        
        self.last_context = "\n---\n".join(context_chunks)
        
        # --- EXTRACTION ---
        prompt = f"""
        Analyze the following text from a NMRA Gazette and extract all medicine price information.
        
        **CONTEXT:**
        {self.last_context[:10000]} # Increased context limit
        
        **INSTRUCTIONS:**
        1. Identify the 'Generic Name' (Active Ingredient), 'Strength/Dosage', and 'Maximum Retail Price' (MRP).
        2. Even if the text is structured as sentences instead of a table, find the specific prices.
        3. Identify any 'Removed' or 'Deregistered' products.
        
        **FORMAT (Pipe-separated):**
        CHANGE | [Active Ingredient] | [Strength] | [New MRP]
        NEW | [Active Ingredient] | [Strength] | [MRP]
        REMOVED | [Active Ingredient] | [Strength]
        DEADLINE | [Date]
        
        Wait! If you find tables with columns, be very precise in matching the medicine name to its specific row price.
        """
        
        try:
            response = self.chatbot.llm.invoke(prompt)
            self.last_raw_response = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            self.last_raw_response = f"LLM Error: {str(e)}"
            return []
            
        findings = self._parse_findings(self.last_raw_response)
        deadline = self._extract_deadline(self.last_raw_response)
        self.last_raw_findings = findings
        
        # --- MATCHING & IMPACT ---
        impacted_products = []
        for record in findings:
            if record['type'] in ['CHANGE', 'REMOVED']:
                matches = self._find_matches(record)
                for _, product in matches.iterrows():
                    impact_data = self._analyze_single_product_impact(product, record, deadline)
                    impacted_products.append(impact_data)
            elif record['type'] == 'NEW':
                is_existing = not self._find_matches(record).empty
                if not is_existing:
                    impacted_products.append(self._create_opportunity_impact(record, deadline))

        return impacted_products

    def get_last_raw_llm_response(self):
        return self.last_raw_response

    def get_last_retrieved_context(self):
        return self.last_context

    def _parse_findings(self, text):
        results = []
        for line in text.split('\n'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                ctype = parts[0].upper()
                if ctype in ['CHANGE', 'NEW', 'REMOVED']:
                    item = {'type': ctype, 'ingredient': parts[1], 'strength': parts[2]}
                    if ctype in ['CHANGE', 'NEW'] and len(parts) >= 4:
                        # Clean price string
                        price_val = re.sub(r'[^\d.]', '', parts[3])
                        item['price'] = price_val if price_val else "0"
                    results.append(item)
        return results

    def _extract_deadline(self, text):
        match = re.search(r"DEADLINE\s*\|\s*(.+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else "TBD"

    def _find_matches(self, record):
        """Standardized matching on ingredient (Step 6)"""
        ingredient = record['ingredient'].lower().strip()
        def check_row(row):
            cat_ingredient = str(row['active_ingredient']).lower()
            return ingredient in cat_ingredient or cat_ingredient in ingredient
        return self.products_df[self.products_df.apply(check_row, axis=1)]

    def _analyze_single_product_impact(self, product, record, deadline):
        curr_mrp = float(product['current_mrp']) if pd.notnull(product['current_mrp']) else 0
        new_mrp = float(record.get('price', 0))
        
        if record['type'] == 'REMOVED':
            impact_type = "PRODUCT REMOVED"
            priority = "CRITICAL"
            effort = "3-5h"
            new_mrp = 0
        elif new_mrp < curr_mrp:
            impact_type = "PRICE DECREASE"
            priority = "HIGH"
            effort = "2-4h"
        elif new_mrp > curr_mrp:
            impact_type = "PRICE INCREASE"
            priority = "MEDIUM"
            effort = "1-2h"
        else:
            impact_type = "NO CHANGE"
            priority = "LOW"
            effort = "<1h"

        return {
            "brand": product['product_brand'],
            "ingredient": product['active_ingredient'],
            "old_price": curr_mrp,
            "new_price": new_mrp,
            "impact_type": impact_type,
            "priority": priority,
            "effort": effort,
            "deadline": deadline,
            "action_plan": self._generate_plan(impact_type, deadline)
        }

    def _create_opportunity_impact(self, record, deadline):
        return {
            "brand": "New Opportunity",
            "ingredient": f"{record['ingredient']} ({record['strength']})",
            "old_price": 0,
            "new_price": float(record.get('price', 0)),
            "impact_type": "NEW PRODUCT OPPORTUNITY",
            "priority": "LOW",
            "effort": "2-3h",
            "deadline": deadline,
            "action_plan": self._generate_plan("NEW PRODUCT OPPORTUNITY", deadline)
        }

    def _generate_plan(self, impact_type, deadline):
        plans = {
            "PRICE DECREASE": [f"Update ERP by {deadline}", "Update pharmacy tags", "Notify distributors"],
            "PRICE INCREASE": [f"Update ERP by {deadline}", "Update price tags"],
            "PRODUCT REMOVED": ["STOP imports", "Check inventory", "Notify distributors"],
            "NEW PRODUCT OPPORTUNITY": ["Evaluate business case", "Check supplier"],
            "NO CHANGE": ["Monitor."]
        }
        return plans.get(impact_type, ["Review changes."])
