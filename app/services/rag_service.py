from sqlalchemy import text
from app.db.session import SessionLocal

def retrieve_relevant_docs(db, embedding):
    return db.execute(
        text("""
        SELECT content
        FROM knowledge_base
        ORDER BY embedding <-> CAST(:embedding AS vector)
        LIMIT 3
        """),
        {"embedding": embedding}
    ).fetchall()


def retrieve_keyword_docs(db, query):
    return db.execute(
        text("""
        SELECT content
        FROM knowledge_base
        WHERE to_tsvector('english', content)
        @@ plainto_tsquery(:query)
        LIMIT 5
        """),
        {"query": query}
    ).fetchall()
def hybrid_retrieval(embedding, query):
    db = SessionLocal()

    try:
        vector_docs = retrieve_relevant_docs(db, embedding)
        keyword_docs = retrieve_keyword_docs(db, query)

        unique_docs = list({
            row[0]
            for row in vector_docs + keyword_docs
        })

        return unique_docs

    finally:
        db.close()