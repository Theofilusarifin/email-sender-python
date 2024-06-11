from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from email.message import EmailMessage
import ssl
import smtplib
import re
import logging
import uvicorn

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailBody(BaseModel):
    subject: str
    body: str
    receivers: List[str]

class EmailSender:
    def __init__(self):
        self.email_sender = os.environ.get("EMAIL_SENDER")
        self.email_password = os.environ.get("EMAIL_PASSWORD")
        self.email_receivers = []

        if not self.email_sender or not self.email_password:
            logger.error("EMAIL_SENDER and EMAIL_PASSWORD environment variables must be set.")
            raise ValueError("EMAIL_SENDER and EMAIL_PASSWORD environment variables must be set")

    def set_email_receivers(self, receivers):
        for receiver in receivers:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", receiver):
                logger.error(f"Invalid email address: {receiver}")
                raise HTTPException(status_code=400, detail=f"Invalid email address: {receiver}")
        self.email_receivers = receivers

    def set_email_subject(self, subject):
        self.email_subject = subject

    def set_email_body(self, body):
        self.email_body = self.format_email_body(body)

    def format_email_body(self, body):
        formatted_body = body.replace("\\n", "<br>")  # Example: Replace newline with <br> tag
        return formatted_body

    def send_email(self):
        em = EmailMessage()
        em['From'] = self.email_sender
        em['To'] = ", ".join(self.email_receivers)
        em['Subject'] = self.email_subject
        
        # Set HTML content
        em.add_alternative(self.email_body, subtype='html')

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(self.email_sender, self.email_password)
                smtp.sendmail(self.email_sender, self.email_receivers, em.as_string())
                logger.info("Email sent successfully.")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            raise HTTPException(status_code=500, detail="SMTP error occurred")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(status_code=500, detail="Failed to send email")

email_sender = EmailSender()

# Endpoint to send email
@app.post("/send_email/")
async def send_email_route(email_body: EmailBody):
    try:
        email_sender.set_email_subject(email_body.subject)
        email_sender.set_email_body(email_body.body)
        email_sender.set_email_receivers(email_body.receivers)  
        email_sender.send_email()
        return {"message": "Email sent successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"An error occurred in send_email_route: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email") from e

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8021, reload=True)
