# AI-Powered Interview Accelerator

A comprehensive AI-powered interview preparation platform that helps students and job candidates prepare for specific job interviews through personalized, adaptive AI interviews.

## Features

### 🎯 Core Features
- **Job Description Analysis** - AI extracts role, responsibilities, required/preferred skills, competencies, keywords
- **Resume Analysis** - AI analyzes candidate's skills, experience, projects, achievements, strengths, gaps
- **Job Fit Assessment** - Weighted scoring (Required Skills 50%, Preferred 20%, Experience 15%, Strengths 15%)
- **3-Level Adaptive Interview**:
  - **Level 1 - Screening** (5 Qs): Resume-specific, motivation, basic fit
  - **Level 2 - Competency** (7 Qs): Technical depth, problem-solving, STAR behavioral
  - **Level 3 - Deep Dive** (10 Qs): Challenges, "why/how", scenarios, trade-offs
- **Dynamic Follow-ups** - AI generates follow-up questions based on candidate's answers
- **Difficulty Adaptation** - Questions get harder/easier based on performance
- **Voice AI** - Browser Speech Recognition (STT) + SpeechSynthesis (TTS)
- **Video Interview** - WebRTC via LiveKit with camera/mic controls
- **Comprehensive Evaluation** - 7 competency scores, question-level feedback, preparation gaps, readiness assessment

### 🔧 Technical Stack

**Frontend:**
- Next.js 14+ (App Router, TypeScript)
- Tailwind CSS + Radix UI primitives
- NextAuth.js (credentials provider)
- Web Speech API (STT) + SpeechSynthesis (TTS)
- LiveKit Client (WebRTC video)

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 + PostgreSQL + pgvector
- Pydantic v2 for validation
- Alembic migrations
- LLM Providers: Nemotron 3 Ultra 550B (primary), OpenAI/Anthropic/Gemini (fallback)

**Infrastructure:**
- Docker Compose (PostgreSQL, Redis, MinIO)
- JWT Authentication
- MinIO/S3 file storage

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Using Docker Compose (Recommended)
```bash
# Clone and start all services
git clone https://github.com/Pavneesh52/Interview-Accelerator.git
cd Interview-Accelerator
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Local Development

**Backend:**
```bash
cd backend
cp .env.example .env
# Edit .env with your settings
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Dashboard│ │ Upload   │ │Interview │ │ Results  │       │
│  │  Page    │ │  Page    │ │  Screen  │ │  Page    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│         │           │           │           │                │
│         ▼           ▼           ▼           ▼                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Client-Side Voice/Video Engine              │   │
│  │  Web Speech API (STT) │ SpeechSynthesis (TTS) │WebRTC│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    HTTPS / WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                       │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │  Document  │ │  Analysis  │ │ Interview  │ │Evaluation│ │
│  │ Processor  │ │  Engine    │ │  Engine    │ │ Engine   │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
│         │           │           │           │                │
│         ▼           ▼           ▼           ▼                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Nemotron 3 Ultra 550B (LLM)             │   │
│  │  - Structured Output (JSON Schema)                   │   │
│  │  - Function Calling for Tools                        │   │
│  │  - Long Context (128k+) for Full Interview History   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   POSTGRESQL + PGVECTOR                     │
│  Users │ Sessions │ Documents │ Analysis │ Interviews │Reports│
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Documents
- `POST /api/v1/documents/jd/upload` - Upload JD file (PDF/DOCX/TXT)
- `POST /api/v1/documents/jd/paste` - Paste JD text
- `POST /api/v1/documents/resume/upload` - Upload resume file
- `POST /api/v1/documents/resume/paste` - Paste resume text
- `GET /api/v1/documents/jd/{id}` - Get JD details
- `GET /api/v1/documents/resume/{id}` - Get resume details

### Analysis
- `POST /api/v1/analysis/sessions` - Create analysis session
- `GET /api/v1/analysis/sessions` - List user sessions
- `GET /api/v1/analysis/sessions/{id}` - Get session with all analyses
- `POST /api/v1/analysis/sessions/{id}/analyze` - Run AI analysis
- `GET /api/v1/analysis/sessions/{id}/jd-analysis` - Get JD analysis
- `GET /api/v1/analysis/sessions/{id}/resume-analysis` - Get resume analysis
- `GET /api/v1/analysis/sessions/{id}/job-fit` - Get job fit assessment

### Interviews
- `POST /api/v1/interviews/start` - Start new interview
- `GET /api/v1/interviews/{id}` - Get interview state
- `POST /api/v1/interviews/questions/{id}/answer` - Submit answer
- `POST /api/v1/interviews/{id}/next-question` - Get next question (handles follow-ups)
- `POST /api/v1/interviews/{id}/evaluate` - Generate full evaluation
- `POST /api/v1/interviews/{id}/complete` - Mark interview complete

### Video
- `POST /api/v1/video/interviews/{id}/video-token` - Get LiveKit token

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/interview_agent
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-min-32-chars
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=interview-agent
NEMOTRON_API_BASE=http://localhost:8001/v1
NEMOTRON_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LIVEKIT_URL=wss://your-livekit-server.com
```

### Frontend (.env)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret-min-32-chars
```

## Deployment

### Production Checklist
- [ ] Set strong SECRET_KEY and NEXTAUTH_SECRET
- [ ] Configure production DATABASE_URL
- [ ] Set up S3/MinIO for file storage
- [ ] Configure LLM API keys (Nemotron, OpenAI, Anthropic, Gemini)
- [ ] Set up LiveKit Cloud or self-hosted LiveKit
- [ ] Configure CORS origins
- [ ] Enable HTTPS
- [ ] Set up monitoring/logging

### Vercel (Frontend) + Railway/Render (Backend)
1. Connect GitHub repo to Vercel
2. Add environment variables
3. Deploy backend to Railway/Render
4. Update NEXT_PUBLIC_API_URL

## Project Structure

```
Interview-Accelerator/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Configuration
│   │   ├── db/              # Database session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Migrations
│   ├── pyproject.toml       # Poetry config
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities, API, types
│   │   └── globals.css      # Tailwind styles
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Evaluation Methodology

### Job Fit Scoring
```
Score = Required_Skills_Match(50%) + Preferred_Skills_Match(20%) 
      + Experience_Relevance(15%) + Strengths_Bonus(15%)
```

### Interview Competencies (7)
1. **Role Fit** - Alignment with JD requirements
2. **Technical Knowledge** - Depth and accuracy
3. **Problem Solving** - Approach to complex problems
4. **Communication** - Clarity and structure
5. **Confidence** - Self-assurance in responses
6. **Depth of Understanding** - Beyond surface level
7. **Behavioral Fit** - Soft skills alignment

### Readiness Levels
- 🔴 **Not Ready** (< 55) - Significant preparation required
- 🟠 **Needs Preparation** (55-69) - Important gaps remain
- 🟡 **Interview Ready** (70-84) - Can reasonably attempt
- 🟢 **Strong Candidate** (≥ 85) - Strong readiness

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details.