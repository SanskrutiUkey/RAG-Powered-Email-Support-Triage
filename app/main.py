from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI

import os
from app.db.session import engine, Base
from app.api.webhooks.resend import router as resend_webhook_router
from app.api.admin.routes import router as admin_router
from app.db.models import SupportTicket, KnowledgeBase

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(resend_webhook_router)
app.include_router(admin_router)

INBOX_DB_ID = os.getenv("INBOX_DB_ID")
PRODUCT_KB_DB_ID = os.getenv("PRODUCT_KB_DB_ID")

@app.get("/")
def root():
    return {"message": "Side Hustle Ops Engine ✅"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/lead")
async def create_lead(sender: str, message: str):
    # Create row in Inbox & Leads DB
    result = notion.pages.create(
        parent={"database_id": INBOX_DB_ID},
        properties={
            "Sender": {"rich_text": [{"text": {"content": sender}}]},
            "Message": {"rich_text": [{"text": {"content": message}}]},
            "Status": {"status": {"name": "New"}},
        },
    )
    return {"Status": "Lead created ✅", "page_id": result["id"]}

from pydantic import BaseModel


class ApproveRequest(BaseModel):
    page_id: str
    sender: str
    draft_reply: str


@app.head("/ai-agent")
async def ai_agent():
    new_leads = notion.databases.query(
        database_id=INBOX_DB_ID,
        filter={"property": "Status", "status": {"equals": "New"}},
    )

    results = []
    for lead in new_leads["results"]:
        sender_prop = lead["properties"]["Sender"]
        if "rich_text" in sender_prop and sender_prop["rich_text"]:
            sender = sender_prop["rich_text"][0]["plain_text"]
            name = (
                sender.split("@")[0].capitalize()
                if "@" in sender
                else sender.split()[0].capitalize()
            )
        elif "title" in sender_prop and sender_prop["title"]:
            sender = sender_prop["title"][0]["plain_text"]
            name = sender.split()[0].capitalize()
        else:
            sender = "user@example.com"
            name = "User"

        message = lead["properties"]["Message"]["rich_text"][0]["plain_text"]

        # MCP: Search Product KB for context
        kb_search = notion.databases.query(
            database_id=PRODUCT_KB_DB_ID,
            filter={
                "or": [
                    {"property": "Tags", "multi_select": {"contains": "Lead"}},
                    {"property": "Tags", "multi_select": {"contains": "Pricing"}},
                    {"property": "Tags", "multi_select": {"contains": "Setup"}},
                    {"property": "Tags", "multi_select": {"contains": "Features"}},
                    {"property": "Tags", "multi_select": {"contains": "Support"}},
                ]
            },
        )

        kb_context = []
        for kb in kb_search["results"][:3]:
            content_prop = kb["properties"].get("Content", {})
            if content_prop.get("rich_text") and content_prop["rich_text"]:
                kb_context.append(content_prop["rich_text"][0]["plain_text"])
            else:
                kb_context.append("No content found")

        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        # OpenAI generates reply
        prompt = f"""User asked: "{message}"
Search Product KB for relevant info: {kb_context}

Generate reply:
- Match USER question exactly (pricing, setup, features)
- Use ONLY KB context  
- Friendly, <80 words
- Sign off: "Ask me anything! 🚀" """

        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        draft = response.choices[0].message.content

        # Update Notion row
        kb_urls = [kb["url"] for kb in kb_search["results"][:3]]

        notion.pages.update(
            page_id=lead["id"],
            properties={
                "Draft Reply": {"rich_text": [{"text": {"content": draft}}]},
                "Kb Links": {
                    "url": kb_urls[0] if kb_urls else "https://notion.so/your-kb"
                },  # Link to KB
                "Status": {"status": {"name": "Ready"}},
            },
        )
        results.append(f"AI replied to {name}")

    return {"processed": results}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
