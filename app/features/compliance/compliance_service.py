import re
import json
from datetime import datetime
from services.audit_service import AuditService
from services.notification_service import NotificationService

class ComplianceService:
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.audit_service = AuditService()
        self.notification_service = NotificationService()
        self.extracted_rules = [] # Cache for Step 1

    def extract_rules(self):
        """
        Step 1: Regulation Extraction.
        Extracts relevant regulatory rules from NMRA price gazettes (PDFs).
        """
        prompt = """
        Scan all loaded NMRA gazettes and extract the key regulatory rules into a structured format.
        Focus on:
        1. Medicine Names and their Ceiling Prices (MRP).
        2. Implementation Deadlines.
        3. Regulatory Requirements (Approvals needed, Import rules).
        
        Provide the output as a structured list of JSON objects:
        - {"type": "Price", "subject": "Drug X", "value": "Rs. 10.00", "rule": "Maximum Retail Price"}
        - {"type": "Requirement", "subject": "Import", "rule": "Marketing Authorization required"}
        """
        
        response = self.chatbot.query(prompt)
        if "error" in response:
            return []
            
        try:
            # Extract JSON-like structures from the answer
            json_match = re.findall(r'(\{.+\})', response["answer"])
            self.extracted_rules = [json.loads(j) for j in json_match]
            return self.extracted_rules
        except:
            # Fallback to simple list if JSON parsing fails
            self.extracted_rules = [{"note": "Rules extracted but parsing failed", "content": response["answer"]}]
            return self.extracted_rules

    def assess_risk(self, action_description, category):
        """
        Steps 3 & 4: Regulation-Action Comparison and Risk Scoring.
        Compares the proposed action with extracted regulations and assigns a risk score.
        """
        # Ensure rules are extracted for context (Step 1)
        if not self.extracted_rules:
            self.extract_rules()
            
        prompt = f"""
        You are a Compliance Risk Assessor for Hemas Pharmaceuticals.
        
        **Action to Evaluate:**
        {action_description}
        **Category:** {category}
        
        **Your Workflow (Steps 3 & 4):**
        1. Compare this action with the requirements from the latest NMRA gazettes.
        2. Identify specific DISCREPANCIES (e.g., missing approvals, pricing mismatch).
        3. Assign a RISK SCORE: Low, Medium, or High based on:
           - Compliance Gap Severity
           - Urgency of Violation
        4. Provide CITATIONS from the source documents for each rule.
        5. Provide CORRECTIVE ACTIONS to reduce the risk.

        **Format (Strictly follow this):**
        RISK SCORE: [Score]
        
        DISCREPANCIES:
        - [Highlight discrepancies here]
        
        RATIONALE:
        [One or two sentences]
        
        CHECKLIST:
        - [ ] requirement 1
        - [ ] requirement 2
        
        CITATIONS:
        - [Document Name, Page #]
        
        CORRECTIVE ACTIONS:
        1. [Priority action]
        """
        
        # Step 3 & 4: Comparison & Scoring Engine
        response = self.chatbot.query(prompt)
        
        if "error" in response:
            return {"error": response["error"]}
            
        answer = response["answer"]
        
        # Parse Score
        score_match = re.search(r"RISK SCORE:\s*(Low|Medium|High)", answer, re.IGNORECASE)
        risk_score = score_match.group(1) if score_match else "Medium"
        
        # Step 5: Feedback and ALERTS
        if risk_score == "High":
            self.notification_service.send_email_alert(
                recipient="head-of-compliance@hemas.com",
                risk_score=risk_score,
                action_description=action_description,
                assessment=answer
            )
            
        # Step 6: AUDIT TRAIL
        self.audit_service.log_assessment(
            action_description=action_description,
            category=category,
            risk_score=risk_score,
            rationale=answer,
            citations=response.get("sources", []),
            corrective_actions=answer # Simplified for now
        )
        
        return {
            "risk_score": risk_score,
            "assessment": answer,
            "sources": response.get("sources", [])
        }

    def get_audit_logs(self):
        """Step 6: Retrieve the Audit Trail"""
        return self.audit_service.get_logs()
