import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SENDER_EMAIL, SENDER_PWD, SERVER_HOST, SERVER_PORT, SENDER_NAME

def compose_body_error_instance(client_email, instance, message):
    return f"""
                Dear {client_email},

                We are pleased to inform you that the processing of your instance on Vast AI has been error.

                Instance ID: {instance['id']}
                Image: {instance['image_uuid']}
                Error Message: {message}
                
                You now have the option to either:

                1. Delete the instance (This will permanently remove it from the system).
                2. Stop the instance (This will halt its current execution, but it can be resumed later).
                
                If you have any questions or need further assistance, feel free to reach out to our support team.

                Best regards,
                iSE Laboratory
            """

def compose_subject_error_instance(instance_id):
    return f"Notification about the process of the instance {instance_id} on Vast AI has been error."

def compose_body_finished_instance(client_email, instance):
    return f"""
                Dear {client_email},

                We are pleased to inform you that the processing of your instance on Vast AI has been completed.

                Instance ID: {instance['id']}
                Image: {instance['image_uuid']}
                
                You now have the option to either:

                1. Delete the instance (This will permanently remove it from the system).
                2. Stop the instance (This will halt its current execution, but it can be resumed later).
                
                If you have any questions or need further assistance, feel free to reach out to our support team.

                Best regards,
                iSE Laboratory
            """

def compose_subject_finished_instance(instance_id):
    return f"Notification about the process of the instance {instance_id} on Vast AI has been completed."

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
        