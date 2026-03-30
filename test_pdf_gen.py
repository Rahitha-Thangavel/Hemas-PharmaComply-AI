from reportlab.pdfgen import canvas
import os
from datetime import datetime, timedelta

def create_dummy():
    os.makedirs("data", exist_ok=True)
    c = canvas.Canvas("data/dummy_test.pdf")
    
    # Yellow deadline
    d1 = datetime.now() + timedelta(days=5)
    # Red deadline
    d2 = datetime.now() + timedelta(days=1)
    
    c.drawString(100, 750, "NMRA Gazette Notification")
    c.drawString(100, 700, f"Drug prices must be implemented by {d1.strftime('%Y-%m-%d')}.")
    c.drawString(100, 650, f"Import licenses must be renewed before {d2.strftime('%Y-%m-%d')} immediately.")
    
    c.save()
    print("Dummy PDF created")

if __name__ == "__main__":
    create_dummy()
