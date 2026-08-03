import json
import os
import asyncio
import requests
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from svix.webhooks import Webhook
from app.db.session import get_db
from app.db.models import SupportTicket
from app.core.tasks import process_support_email
from app.core.redis import redis_client
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
@router.post("/resend")
async def resend_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.body()
        headers = {
            "svix-id": request.headers.get("svix-id"),
            "svix-timestamp": request.headers.get("svix-timestamp"),
            "svix-signature": request.headers.get("svix-signature"),
        }

        if not all(headers.values()):
            raise HTTPException(status_code=400, detail="Missing svix headers")

        webhook_id = request.headers.get("svix-id")

        def _check_dedup():
            return redis_client.get(f"webhook:{webhook_id}")

        existing = await asyncio.to_thread(_check_dedup)
        if existing:
            return {"ok": True, "duplicate": True}

        webhook_secret = os.getenv("RESEND_WEBHOOK_SECRET")
        if not webhook_secret:
            raise HTTPException(status_code=500, detail="Webhook secret not configured")

        wh = Webhook(webhook_secret)
        verified_payload = wh.verify(payload.decode("utf-8"), headers)

        if type(verified_payload) == dict:
            data = verified_payload
        else:
            data = json.loads(verified_payload)

        payload_data = data.get("data")
        if payload_data is None:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")

        email_id = payload_data.get("email_id")
        sender = payload_data.get("from")
        subject = payload_data.get("subject")

        # Fetch Text body & html body from Resend API using email_id
        text_body = None
        html_body = None

        if email_id:
            resend_response = requests.get(
                f"https://api.resend.com/emails/receiving/{email_id}",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}"
                },
                timeout=10
            )


            if resend_response.status_code == 200:
                email_data = resend_response.json()

                text_body = email_data.get("text")
                html_body = email_data.get("html")

        ticket = SupportTicket(
            email_id=email_id,
            sender=sender,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            raw_payload=data,
            processing_status="pending",
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        job_data = {
            "ticket_id": ticket.id,
            "email_id": email_id,
            "sender": sender,
            "subject": subject,
            "text_body": text_body,
        }

        def _set_dedup():
            redis_client.setex(
                f"webhook:{webhook_id}",
                86400,
                "processed"
            )

        await asyncio.to_thread(_set_dedup)

        process_support_email.apply_async(
            args=[job_data],
            queue="ai_processing"
        )

        return {"ok": True, "ticket_id": ticket.id}

    except Exception as e:
        db.rollback()
        print("WEBHOOK ERROR:", repr(e))
        raise