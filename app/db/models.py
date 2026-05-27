from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from app.db.session import Base
from pgvector.sqlalchemy import Vector

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String(255), unique=True, nullable=False, index=True)
    sender = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    text_body = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    processing_status = Column(String(50), nullable=False, default="pending")
    ai_draft = Column(Text, nullable=True)
    error_reason = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    embedding = Column(Vector(768))