# RAG-Powered Email Support Platform

An AI-powered customer support automation platform that ingests incoming emails, retrieves relevant knowledge base content using RAG, generates AI-assisted support drafts, and enables human review before sending responses.

---

## Features

- Email ingestion via webhook
- Asynchronous processing using Celery + Redis
- Retrieval-Augmented Generation (RAG)
- Vector search with PostgreSQL + pgvector
- Cross-encoder reranking for improved retrieval quality
- Human-in-the-loop review workflow
- Role-based access control (Admin / Agent)
- Retry handling and Dead Letter Queue (DLQ)
- Queue separation for AI processing and email delivery
- Dockerized deployment

---

## Architecture

```text
Incoming Email
      │
      ▼
Webhook Endpoint (FastAPI)
      │
      ▼
PostgreSQL
(Store Ticket)
      │
      ▼
Redis Queue
      │
      ▼
Celery Worker
      │
      ├─────────────── Generate Embedding
      │
      ├─────────────── Hybrid Search
      │                    │
      │                    ├─ Vector Search (pgvector)
      │                    └─ Keyword Search (BM25)
      │
      ├─────────────── Reranking
      │
      ├─────────────── Gemini/OpenAI
      │
      ▼
AI Draft Generated
      │
      ▼
Admin / Agent Dashboard
      │
      ├─ Approve & Send
      └─ Reject
      │
      ▼
Resend Email API
      │
      ▼
Customer Response


Failure Flow

Celery Task
      │
      ▼
Retry (3x)
      │
      ▼
Dead Letter Queue
      │
      ▼
Admin Replay
```

---

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- pgvector

### Async Processing

- Celery
- Redis

### AI / RAG

- Gemini API
- Vector Embeddings
- Hybrid Search
- Cross Encoder Reranking

### Infrastructure

- Docker
- Docker Compose

---

## Key Engineering Decisions

### Why Celery + Redis instead of Kafka?

The system requires reliable background task execution rather than large-scale event streaming.

Celery + Redis provides:

- Simpler operational model
- Built-in retries
- Queue separation
- Lower infrastructure complexity

for the workload requirements of an AI support platform.

---

### Why Hybrid Search?

Vector search captures semantic meaning while keyword search captures exact business terminology.

Combining both improves retrieval quality for:

- Product names
- Plan names
- Error codes
- Internal policies

---

### Why Reranking?

Hybrid search retrieves candidate documents.

A cross-encoder reranker selects the most relevant documents before sending context to the LLM, reducing noisy context and improving response quality.

---

## Security

- JWT Authentication
- Role-Based Access Control (RBAC)
- Admin / Agent permissions
- Protected dashboard endpoints

---

## Scalability Features

- Multiple Celery workers
- Queue separation
- Dead Letter Queue (DLQ)
- Asynchronous processing
- Dockerized services
- Stateless FastAPI application

---

## Local Setup

### Clone

```bash
git clone <repository-url>
cd project
```

### Install

```bash
pip install -r requirements.txt
```

### Start Services

```bash
docker compose up --build
```

### Run FastAPI

```bash
uvicorn app.main:app --reload
```

### Run Celery Worker

```bash
celery -A app.core.celery_app worker --loglevel=info
```

---

## Testing

```bash
pytest
```

Tests cover:

- RAG retrieval
- Reranking pipeline
- End-to-end email processing flow

---

## Future Improvements

- Prometheus + Grafana monitoring
- Kubernetes deployment
- Cloud object storage (S3 / R2)
- Auto-scaling workers
- Advanced agentic RAG workflows

---

## Resume Highlights

- Built a RAG-powered email support automation platform using FastAPI, Celery, Redis, PostgreSQL + pgvector, and Gemini/OpenAI.
- Designed an asynchronous processing pipeline with retries, queue separation, and Dead Letter Queue support.
- Implemented hybrid retrieval and cross-encoder reranking to improve context relevance before LLM-based response generation.
- Developed role-based access control and a human-in-the-loop workflow for support-agent review and approval.