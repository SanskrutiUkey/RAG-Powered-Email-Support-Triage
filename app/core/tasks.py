import logging
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

from app.core.celery_app import celery
from app.db.models import SupportTicket
from app.db.session import SessionLocal
from app.services.rag_service import retrieve_relevant_docs
from app.services.email_service import send_support_reply
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
        start_time = time.time()
        ticket_id = job_data["ticket_id"]

        ticket = (
            db.query(SupportTicket)
            .filter(SupportTicket.id == ticket_id)
            .first()
        )
        print("Processing ticket:", ticket.text_body, ticket.id)
        if not ticket:
            return

        # Generate embedding for incoming email      
        email_embedding_response = client.embeddings.create(
            model="gemini-embedding-001",
            input=ticket.text_body,
            dimensions=768
        )

        email_embedding = (email_embedding_response.data[0].embedding)

        # Retrieve relevant KB docs
        docs = retrieve_relevant_docs(db, email_embedding)
        docs = [row[0] for row in docs]

        # Lazy import reranking service
        from app.services.reranking_service import rerank_docs
        docs = rerank_docs(
            ticket.text_body,
            docs,
            top_k=3
        )

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

        ai_reply = (response.choices[0].message.content)

        if ai_reply:
            ticket.ai_draft = ai_reply
            ticket.processing_status = "draft_generated" 

            logger.info(f"EMAIL_PROCESSED ticket_id={ticket_id}")
        else:
            logger.error(f"Failed to generate AI reply for ticket {ticket_id}")

        logger.info(f"Task completed in {time.time() - start_time:.2f}s")
        db.commit()

        logger.info("AI draft generated")

    except Exception as e:

        logger.error(f"FAILED: {str(e)}")

        if self.request.retries >= self.max_retries:

            try:
                email_id = job_data.get("email_id")

                ticket = (
                    db.query(SupportTicket)
                    .filter(SupportTicket.email_id == email_id)
                    .first()
                )

                if ticket:
                    ticket.processing_status = "failed"
                    ticket.error_reason = str(e)
                    db.commit()

            except Exception as db_error:

                db.rollback()

                logger.error(f"DB update failed: {str(db_error)}")
                
            dead_letter_task.apply_async(
                args=[job_data, str(e)],
                queue="dead_letter_queue"
            )

            logger.error(f"Moved job to DLQ: {job_data}")
        else:
            logger.warning( f"Retry {self.request.retries + 1}" )
            raise self.retry(
                exc=e,
                countdown=10
            )

    finally:
        db.close()


@celery.task(bind=True, max_retries=3)
def send_support_reply_task(self, to_email, subject, response_text):
    try:
        # Delegate to the email service which talks to Resend
        send_support_reply(to_email, subject, response_text)
    except Exception as e:
        logger.error(f"FAILED sending reply: {str(e)}")
        raise self.retry(exc=e, countdown=10)

@celery.task
def dead_letter_task(job_data, error):
    logger.error(f"DLQ: {job_data} | Error: {error}")