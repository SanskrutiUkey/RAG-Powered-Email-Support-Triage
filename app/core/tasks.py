import logging
import os

from openai import OpenAI
from dotenv import load_dotenv

from app.core.celery_app import celery
from app.db.models import SupportTicket
from app.db.session import SessionLocal
from app.services.rag_service import retrieve_relevant_docs

logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

@celery.task(bind=True, max_retries=3)
def process_support_email(self, job_data):

    db = SessionLocal()

    try:
        ticket_id = job_data["ticket_id"]

        ticket = (
            db.query(SupportTicket)
            .filter(SupportTicket.id == ticket_id)
            .first()
        )

        if not ticket:
            return

        # Generate embedding for incoming email
        email_embedding_response = client.embeddings.create(
            model="gemini-embedding-001",
            input=ticket.text_body,
            dimensions=768
        )

        email_embedding = (
            email_embedding_response
            .data[0]
            .embedding
        )

        # Retrieve relevant KB docs
        docs = retrieve_relevant_docs(email_embedding)

        retrieved_context = "\n".join(docs)

        # Final grounded prompt
        prompt = f"""
        Customer Email:
        {ticket.text_body}

        Knowledge Base Context:
        {retrieved_context}

        Generate a professional support reply.
        """

        response = client.chat.completions.create(
            model="gemini-2.5-pro",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        ai_reply = (
            response
            .choices[0]
            .message
            .content
        )

        ticket.ai_draft = ai_reply
        ticket.processing_status = "draft_generated"

        db.commit()

        logger.info("AI draft generated")

    except Exception as e:

        logger.error(f"FAILED: {str(e)}")

        if self.request.retries >= self.max_retries:

            try:
                email_id = job_data.get("email_id")

                ticket = (
                    db.query(SupportTicket)
                    .filter(
                        SupportTicket.email_id == email_id
                    )
                    .first()
                )

                if ticket:
                    ticket.processing_status = "failed"
                    ticket.error_reason = str(e)

                    db.commit()

            except Exception as db_error:

                db.rollback()

                logger.error(
                    f"DB update failed: {str(db_error)}"
                )

        raise self.retry(
            exc=e,
            countdown=10
        )

    finally:
        db.close()