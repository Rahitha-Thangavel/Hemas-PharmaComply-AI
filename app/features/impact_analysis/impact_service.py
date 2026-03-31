import pandas as pd
import os
import re

class ImpactService:
    def __init__(self, chatbot, products_csv_path):
        self.chatbot = chatbot
        self.products_csv_path = products_csv_path
        self.products_df = self._load_products()

    def _load_products(self):
        if os.path.exists(self.products_csv_path):
            return pd.read_csv(self.products_csv_path)
        return pd.DataFrame(columns=["Product Name", "Generic Name", "Current MRP", "Dosage Form", "Strength"])

    def predict_impact(self):
        """
        Maps gazette price changes to actual products and predicts impact.
        """
        # 1. Get price updates from chatbot
        prompt = """
        Extract all medicine price changes from the latest NMRA gazettes.
        Provide a list in the following format:
        - [Generic Name] | [Strength] | [New Ceiling Price]
        
        Example:
        - Paracetamol | 500mg | 6.50
        """
        
        response = self.chatbot.query(prompt)
        
        if "error" in response:
            return []
            
        updates_text = response["answer"]
        updates = []
        for line in updates_text.split('\n'):
            if "|" in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    updates.append({
                        "generic": parts[0].strip('- '),
                        "strength": parts[1],
                        "new_price": parts[2]
                    })
        
        # 2. Map to internal products
        impacted_products = []
        for _, product in self.products_df.iterrows():
            # Check for matches (simple substring or exact)
            for update in updates:
                if update["generic"].lower() in product["Generic Name"].lower() and \
                   update["strength"].lower() in product["Strength"].lower():
                    
                    old_price = float(product["Current MRP"])
                    try:
                        new_price = float(re.sub(r'[^\d.]', '', update["new_price"]))
                    except:
                        new_price = old_price # Fallback
                        
                    impact_level = "High" if abs(new_price - old_price) / old_price > 0.1 else "Medium"
                    
                    impacted_products.append({
                        "product_name": product["Product Name"],
                        "generic": product["Generic Name"],
                        "current_mrp": old_price,
                        "new_ceiling": new_price,
                        "impact": impact_level,
                        "action_plan": self._generate_action_plan(product["Product Name"], impact_level)
                    })
        
        return impacted_products

    def _generate_action_plan(self, product_name, impact_level):
        """Generates a step-by-step action plan for a product"""
        if impact_level == "High":
            return [
                "Immediate: Halt distribution and stock billing.",
                "Verify new MRP against Gazette No. 2446_34.",
                "Coordinate with supply chain for re-labeling of existing stock.",
                "Update SAP/ERP pricing with new effective date.",
                "Notify all retail and wholesale partners of price adjustment."
            ]
        else:
            return [
                "Verify new MRP in system.",
                "Schedule label updates for next production batch.",
                "Update retail price lists."
            ]
