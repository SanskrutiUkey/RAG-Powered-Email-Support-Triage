from sqlalchemy import text
from app.db.session import SessionLocal

def retrieve_relevant_docs(embedding):

    db = SessionLocal()

    try:
        docs = db.execute(
            text("""
            SELECT content
            FROM knowledge_base
            ORDER BY embedding <-> CAST(:embedding AS vector)
            LIMIT 3
            """),
            {
                "embedding": embedding
            }
        ).fetchall()

        return [doc[0] for doc in docs]

    finally:
        db.close()