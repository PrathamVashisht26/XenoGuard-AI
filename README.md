# XenoGuard AI

> Intelligent Global Transaction Validation & Recovery Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![Celery](https://img.shields.io/badge/Celery-5.4-brightgreen?logo=celery)](https://docs.celeryq.dev)

## What This Is

XenoGuard AI is not a CSV validator — it's a **transaction data recovery platform**. It validates international transaction datasets, explains every error in plain English, suggests and applies deterministic fixes, and generates business intelligence about your data quality.

## Features

| Feature | Description |
|---|---|
| 🌍 Country-Aware Phone Validation | Configurable per-country rules (India 10 digits, Singapore 8 digits, UAE 9 digits, etc.) |
| 📅 Multi-Format Date Parsing | Handles YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, timestamps, and more |
| 💡 NLG Explanation Engine | Plain-English error diagnoses — no LLM, fully deterministic |
| 🛠️ Auto-Fix Studio | Before/After diff cards with accept/reject workflow |
| 📊 Health Score Dashboard | 0–100 score with Recharts donut + bar charts |
| 🤖 AI Insight Engine | Template-based business intelligence generation |
| ⚡ Async Chunk Processing | Celery + Redis pipeline, linear horizontal scaling |
| 📄 PDF Report Export | ReportLab-generated validation report with insights |
| 🔍 Audit Trail | Immutable event log, all actions timestamped |

## Tech Stack

**Frontend**: Next.js 14 · TypeScript · Tailwind CSS · shadcn/ui · Recharts  
**Backend**: FastAPI · SQLAlchemy · MySQL 8  
**Queue**: Celery 5 + Redis 7  
**Validation**: Pandas · Custom Python engine  
**PDF**: ReportLab  

## Quick Start

### Prerequisites
- Docker Desktop (for MySQL + Redis)
- Python 3.11+
- Node.js 18+

### 1. Start Infrastructure
```bash
cd backend
docker-compose up -d
```

### 2. Start Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python setup.py
uvicorn app.main:app --reload --port 8000
```

### 3. Start Celery Worker (new terminal)
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info -P threads
```

### 4. Generate Test Dataset
```bash
cd backend
python generate_dataset.py
# Creates: sample_transactions.csv (10,000 rows with intentional errors)
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Open: http://localhost:3000
```

## API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger UI.

## Architecture

```
Upload → Chunk → Validate (parallel) → Explain → Aggregate → Insights → Outputs
         ↕              ↕                                         ↕
       Redis         Celery                                    MySQL
```

## Validation Rules

Rules are configurable via JSON files in `backend/rules/`:

- `phone_rules.json` — per-country digit count + regex
- `date_formats.json` — accepted date format strings
- `payment_modes.json` — valid payment mode list

## Deployment

- **Frontend**: Vercel (`vercel deploy`)
- **Backend API**: Render (Web Service)
- **Celery Worker**: Render (Worker Service)  
- **MySQL**: PlanetScale (serverless MySQL)
- **Redis**: Upstash (serverless Redis)

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Rule-based NLG (no LLM) | Free, deterministic, zero-latency, auditable |
| SSE over WebSockets | Works through Vercel/Railway proxies without upgrade headers |
| Celery for CPU work | Pandas operations are CPU-bound; asyncio would block the event loop |
| S3-ready storage abstraction | One config change switches from local to S3 |
| Chain of Responsibility pattern | Each validator is isolated and independently testable |
