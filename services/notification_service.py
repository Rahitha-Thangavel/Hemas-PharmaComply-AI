import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    def __init__(self, smtp_config=None):
        self.config = smtp_config or {
            "server": "smtp.gmail.com",
            "port": 587,
            "user": "compliance-alerts@hemas.com", # Placeholder
            "password": "your-app-password" # Placeholder
        }

    def send_email_alert(self, recipient, risk_score, action_description, assessment):
        """
        Sends an email alert for High-Risk actions.
        In a real scenario, this would use the config. For now, we'll mock the success.
        """
        subject = f"⚠️ HIGH RISK COMPLIANCE ALERT: {risk_score}"
        body = f"""
        Dear Compliance Officer,
        
        A high-risk action has been detected by Hemas PharmaComply AI.
        
        **Action Description:**
        {action_description}
        
        **Assessment Results:**
        {assessment}
        
        Please take immediate corrective action.
        """
        
        # Mocking the send process
        print(f"DEBUG: Email Alert sent to {recipient} regarding {action_description[:30]}...")
        return True
