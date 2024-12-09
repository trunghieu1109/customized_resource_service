import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SENDER_EMAIL, SENDER_PWD, SERVER_HOST, SERVER_PORT, SENDER_NAME

def send_email(receiver: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    message["To"] = receiver
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "plain"))
    
    server = None
    
    try:
        
        server = smtplib.SMTP_SSL(SERVER_HOST, SERVER_PORT)
    
        server.login(SENDER_EMAIL, SENDER_PWD)
        
        server.sendmail(SENDER_EMAIL, receiver, message.as_string())
        
        return {
            "status": "success",
            "message": f"Send email to {receiver}, subject: {subject}, body: {body} successfully"
        }
    
    except Exception as e:
        return {
            "status": "success",
            "message": f"Send email failed, error: {e}"
        }
    
    finally:
       
        server.quit()
        print("Handle email successfully")
        