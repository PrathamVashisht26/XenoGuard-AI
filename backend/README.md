# XenoGuard AI — Backend

FastAPI + Celery + MySQL transaction validation platform.

## Quick Start (Local)

### 1. Start infrastructure
```bash
docker-compose up -d
```

### 2. Install Python deps
```bash
pip install -r requirements.txt
```

### 3. Generate sample dataset
```bash
python generate_dataset.py
```

### 4. Start API server
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start Celery worker (new terminal)
```bash
celery -A app.workers.celery_app worker --loglevel=info -P threads
```

## API Docs
Visit: http://localhost:8000/docs

## Environment Variables
Copy `.env.example` to `.env` and fill in values.
