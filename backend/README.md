# Interview Agent Backend

FastAPI-based backend for the AI-powered Interview Accelerator.

## Quick Start

### Using Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Local Development
```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
poetry run alembic upgrade head

# Start server
poetry run uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── api/v1/           # API routes
├── core/             # Configuration
├── db/               # Database models & session
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
└── main.py           # FastAPI app
```

## Key Features

- JWT Authentication
- File Upload (PDF, DOCX, TXT) with MinIO/S3
- Document Text Extraction
- LLM-powered JD & Resume Analysis
- Job Fit Assessment
- Interview Engine (3 levels)
- Evaluation & Reporting

## Environment Variables

See `.env.example` for all configuration options.