"""
IP-SAKTI SAHAYAK
Database Models
================
SQLAlchemy ORM models for the prototype. SQLite-backed; designed so the
same models work unmodified against Postgres later.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    display_name = Column(String, default="Guest")
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # "user" | "assistant"
    content = Column(Text)
    domain = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    language = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    confidence_level = Column(String, nullable=True)
    abstained = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"
    id = Column(String, primary_key=True, default=_uuid)
    source_name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    jurisdiction = Column(String)
    domain = Column(String)
    authority = Column(String)
    source_type = Column(String)
    priority = Column(Integer, default=3)
    enabled = Column(Boolean, default=True)
    update_frequency = Column(String, default="weekly")
    last_checked = Column(DateTime, nullable=True)

    documents = relationship("Document", back_populates="source")


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=True)
    title = Column(String)
    url = Column(String, nullable=True)
    doc_type = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    authority = Column(String, nullable=True)
    version = Column(String, nullable=True)
    effective_date = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))

    source = relationship("Source", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(String, primary_key=True, default=_uuid)
    document_id = Column(String, ForeignKey("documents.id"))
    chunk_text = Column(Text)
    section = Column(String, nullable=True)
    page = Column(Integer, nullable=True)
    jurisdiction = Column(String, nullable=True)
    authority = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    vector_index_position = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="chunks")


class SearchLog(Base):
    __tablename__ = "search_logs"
    id = Column(String, primary_key=True, default=_uuid)
    query = Column(Text)
    domain = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    retrieval_count = Column(Integer, default=0)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Citation(Base):
    __tablename__ = "citations"
    id = Column(String, primary_key=True, default=_uuid)
    message_id = Column(String, ForeignKey("messages.id"))
    chunk_id = Column(String, ForeignKey("document_chunks.id"), nullable=True)
    source_name = Column(String, nullable=True)
    section = Column(String, nullable=True)
    url = Column(String, nullable=True)
    verified = Column(Boolean, default=False)

    message = relationship("Message", back_populates="citations")


class RegulationUpdate(Base):
    __tablename__ = "regulation_updates"
    id = Column(String, primary_key=True, default=_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=True)
    title = Column(String)
    previous_version = Column(String, nullable=True)
    new_version = Column(String, nullable=True)
    detected_date = Column(DateTime, default=datetime.utcnow)
    change_summary = Column(Text, nullable=True)
    url = Column(String, nullable=True)


class SavedQuery(Base):
    __tablename__ = "saved_queries"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    query = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=_uuid)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    format = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
