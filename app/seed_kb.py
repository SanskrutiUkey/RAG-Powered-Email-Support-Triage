from openai import OpenAI
from app.db.session import SessionLocal
from app.db.models import KnowledgeBase
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
db = SessionLocal()

docs = [
    "Users can reset passwords from the account settings page.",
    "Refunds are processed within 5 business days.",
    "Subscription cancellation is available from billing settings."
]

for content in docs:

    embedding_response = client.embeddings.create(
        model="gemini-embedding-001",
        input=content,
        dimensions=768
    )

    embedding = embedding_response.data[0].embedding

    kb = KnowledgeBase(
        content=content,
        embedding=embedding
    )

    db.add(kb)

db.commit()
db.close()

print("KB inserted")