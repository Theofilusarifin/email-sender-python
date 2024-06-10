from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from email.message import EmailMessage
import ssl
import smtplib

app = FastAPI()

class EmailBody(BaseModel):
    subject: str
    body: str
    receiver: str

class EmailSender:
    def __init__(self):
        self.email_sender = os.environ.get("EMAIL_SENDER")
        self.email_password = os.environ.get("EMAIL_PASSWORD")
        self.email_receiver = None

    def set_email_receiver(self, receiver):
        self.email_receiver = receiver

    def set_email_subject(self, subject):
        self.email_subject = subject

    def set_email_body(self, body):
        self.email_body = body

    def send_email(self):
        em = EmailMessage()
        em['From'] = self.email_sender
        em['To'] = self.email_receiver
        em['Subject'] = self.email_subject
        em.set_content(self.email_body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(self.email_sender, self.email_password)
                smtp.sendmail(self.email_sender, self.email_receiver, em.as_string())
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to send email")

        return {"message": "Email sent successfully"}

email_sender = EmailSender()

@app.post("/send_email/")
async def send_email_route(email_body: EmailBody):
    email_sender.set_email_subject(email_body.subject)
    email_sender.set_email_body(email_body.body)
    email_sender.set_email_receiver(email_body.receiver)  
    email_sender.send_email()