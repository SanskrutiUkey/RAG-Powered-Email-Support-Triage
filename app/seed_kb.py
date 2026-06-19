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
    "Support tickets are typically responded to within 24 hours.",
    "Two-factor authentication can be enabled for additional account security.",
    "API keys can be generated and managed from the developer dashboard.",
    "The free plan allows up to 100 requests per day.",
    "Premium subscribers receive priority support and higher API limits.",
    "Invoices can be downloaded from the billing history section.",
    "Data exports are available in CSV and JSON formats."
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