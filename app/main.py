from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from app.db.session import engine, Base
from app.api.webhooks.resend import router as resend_webhook_router
from app.api.admin.routes import router as admin_router
from app.auth.routes import router as auth_router

# Store model references
embedding_service = None
reranking_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - do minimal loading
    print("API starting - models will load on first use")
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("API shutting down")

app = FastAPI(lifespan=lifespan)

app.include_router(resend_webhook_router)
app.include_router(admin_router)
app.include_router(auth_router)

INBOX_DB_ID = os.getenv("INBOX_DB_ID")
PRODUCT_KB_DB_ID = os.getenv("PRODUCT_KB_DB_ID")

# Lazy loading functions
async def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
    return embedding_service

async def get_reranking_service():
    global reranking_service
    if reranking_service is None:
        from app.services.reranking_service import ReankingService
        reranking_service = ReankingService()
    return reranking_service

import sys
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
print(f"Memory before imports: {__import__('psutil').Process().memory_info().rss / 1024 / 1024:.1f} MB")

from contextlib import asynccontextmanager
import os
from app.db.session import engine, Base
print(f"Memory after db imports: {__import__('psutil').Process().memory_info().rss / 1024 / 1024:.1f} MB")

from app.api.webhooks.resend import router as resend_webhook_router
print(f"Memory after webhook import: {__import__('psutil').Process().memory_info().rss / 1024 / 1024:.1f} MB")

from app.api.admin.routes import router as admin_router
print(f"Memory after admin import: {__import__('psutil').Process().memory_info().rss / 1024 / 1024:.1f} MB")

from app.auth.routes import router as auth_router
print(f"Memory after auth import: {__import__('psutil').Process().memory_info().rss / 1024 / 1024:.1f} MB")
@app.get("/")
def root():
    return {"message": "Side Hustle Ops Engine ✅"}

@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
