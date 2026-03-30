class ChangeService:
    def __init__(self, chatbot):
        self.chatbot = chatbot

    def detect_changes(self):
        """
        Detects and summarizes changes between new and previous NMRA gazettes.
        """
        prompt = """
        Analyze the loaded NMRA gazettes and identify key changes compared to previous regulations (if mentioned) or summarize the primary updates in the latest documents.
        
        Provide a summarized "What changed?" report.
        Format:
        ### 🔄 Regulation Updates
        - **Update Type**: [Change Description]
        
        ### 📢 New Pricing Rules
        - [Summary of any new pricing formulas or rules]
        
        ### 📅 Procedural Changes
        - [Summary of any changes in registration or licensing procedures]
        """
        
        response = self.chatbot.query(prompt)
        
        if "error" in response:
            return "Unable to detect changes at this time."
            
        return response["answer"]
