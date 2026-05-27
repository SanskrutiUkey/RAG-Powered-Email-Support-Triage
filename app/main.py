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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
