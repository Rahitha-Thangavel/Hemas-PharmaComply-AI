import re
from datetime import datetime

class AlertService:
    def __init__(self, chatbot):
        self.chatbot = chatbot

    def extract_deadlines(self):
        """
        Scans gazette documents to extract implementation dates and regulatory deadlines.
        """
        prompt = """
        Extract all regulatory deadlines and implementation dates mentioned in the NMRA gazettes.
        A deadline is any date by which a price change, registration renewal, or regulatory requirement must be met.
        
        Format your response as a list:
        - [Date] | [Requirement Description] | [Document Source]
        
        Example:
        - 2025-11-20 | Implementation of new MRP for Essential Medicines | Gazette 2025-Nov
        """
        
        response = self.chatbot.query(prompt)
        
        if "error" in response:
            return []
            
        lines = response["answer"].split('\n')
        deadlines = []
        
        for line in lines:
            if "|" in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    date_str = parts[0].strip('- ')
                    deadlines.append({
                        "date": date_str,
                        "description": parts[1],
                        "source": parts[2] if len(parts) > 2 else "Multiple",
                        "status": self._calculate_status(date_str)
                    })
        
        return deadlines

    def _calculate_status(self, date_str):
        """Calculates status based on proximity to current date"""
        try:
            # Try to find a date in the string
            match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
            if not match:
                return "Unknown"
                
            deadline_date = datetime.strptime(match.group(1), '%Y-%m-%d')
            today = datetime.now()
            
            diff = (deadline_date - today).days
            
            if diff < 0:
                return "Overdue"
            elif diff < 7:
                return "Critical"
            elif diff < 30:
                return "Upcoming"
            else:
                return "Safe"
        except:
            return "Pending"
