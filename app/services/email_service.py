import os
import resend
from dotenv import load_dotenv
load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

def send_support_reply(to_email, subject, response_text):

    return resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": to_email,
        "subject": f"Re: {subject}",
        "text": response_text
    })