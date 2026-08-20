# Architecture Decision Records (ADRs)

## ADR-001: Technology Stack Selection

**Status:** Accepted

**Context:** Need to build a full-stack AI interview platform with real-time voice/video capabilities.

**Decision:**
- Frontend: Next.js 14 (App Router, TypeScript, Tailwind CSS)
- Backend: FastAPI (Python 3.11+, Pydantic v2, SQLAlchemy 2.0)
- Database: PostgreSQL + pgvector
- Auth: NextAuth.js (credentials + JWT)
- LLM: NVIDIA Nemotron 3 Ultra 550B (primary), OpenAI/Anthropic/Gemini (fallback)
- Voice: Browser Web Speech API + SpeechSynthesis
- Video: LiveKit WebRTC
- Storage: MinIO (S3-compatible)
- Cache/Queue: Redis + Celery

**Rationale:**
- Next.js provides excellent DX, SSR, and TypeScript support
- FastAPI is ideal for AI/ML backends with async support
- Nemotron 3 Ultra chosen for structured output and reasoning
- Browser-native voice APIs avoid server costs and latency
- LiveKit provides managed WebRTC infrastructure
- PostgreSQL + pgvector supports future semantic search

## ADR-002: LLM Structured Output Approach

**Status:** Accepted

**Context:** Need reliable JSON output from LLM for analysis and question generation.

**Decision:** Use Pydantic models with JSON Schema prompting for all LLM interactions.

**Implementation:**
- Each LLM call defines a Pydantic response model
- System prompt includes JSON schema
- Response parsed and validated via Pydantic
- Fallback to text parsing if JSON fails

**Rationale:**
- Type-safe responses
- Automatic validation
- Easy schema evolution
- Provider-agnostic

## ADR-003: Interview State Machine

**Status:** Accepted

**Context:** Need to manage complex interview flow with 3 levels, follow-ups, and adaptive difficulty.

**Decision:** Centralized interview state in database with clear status transitions.

**States:**
- `NOT_STARTED` → `IN_PROGRESS` → `PAUSED` → `COMPLETED` / `ABANDONED`

**Adaptive Logic:**
- Track `difficulty_adjustment` (-1.0 to +1.0)
- Track `topics_covered`, `weaknesses_identified`, `strengths_confirmed`
- Generate follow-ups when answers are vague, unsubstantiated, or have claims
- Adjust level progression based on performance

## ADR-004: Voice AI - Client-Side Only

**Status:** Accepted

**Context:** Need voice interaction for interview simulation.

**Decision:** Use browser-native Web Speech API (STT) and SpeechSynthesis (TTS) entirely client-side.

**Rationale:**
- Zero server infrastructure cost
- Low latency (no network round-trip)
- Privacy-friendly (audio never leaves browser)
- Works offline for TTS

**Trade-offs:**
- Lower accuracy than server-side Whisper
- Limited voice customization
- Browser compatibility varies

## ADR-005: Video Interview - LiveKit WebRTC

**Status:** Accepted

**Context:** Need real-time video for realistic interview experience.

**Decision:** Use LiveKit (managed SFU) for WebRTC infrastructure.

**Rationale:**
- Managed service reduces operational burden
- Scales automatically
- Provides recording, transcription
- React components available

## ADR-006: Evaluation & Reporting

**Status:** Accepted

**Context:** Need comprehensive, actionable feedback after interview.

**Decision:** Single LLM evaluation pass after interview completion with structured output.

**Evaluation Dimensions (7):**
1. Role Fit
2. Technical Knowledge
3. Problem Solving
4. Communication
5. Confidence
6. Depth of Understanding
7. Behavioral Fit

**Output Structure:**
- Overall score (0-100)
- Per-competency scores
- Question-level feedback (what_good, what_better, ideal_direction)
- Strengths/Weaknesses lists
- Prioritized preparation gaps
- Readiness assessment (4 levels)

## ADR-007: Database Schema Design

**Status:** Accepted

**Context:** Need flexible schema for documents, analyses, interviews, and evaluations.

**Key Tables:**
- `users` - Authentication
- `job_descriptions` + `resumes` - Source documents
- `analysis_sessions` - Links JD + Resume
- `jd_analyses`, `resume_analyses`, `job_fit_assessments` - Analysis results
- `interviews`, `interview_questions`, `interview_answers` - Interview flow
- `interview_evaluations` - Final reports

**Design Principles:**
- UUID primary keys
- JSONB for flexible structured data
- Foreign keys with CASCADE deletes
- Indexes on user_id, session_id, status

## ADR-008: File Storage - S3/MinIO

**Status:** Accepted

**Context:** Need to store uploaded PDF/DOCX files.

**Decision:** Use MinIO (local) / S3 (production) with presigned URLs.

**Implementation:**
- Upload to `/job_descriptions` or `/resumes` prefixes
- Store file URL in database
- Validate file type and size (10MB max)
- Extract text on upload, store raw text

## ADR-009: Authentication - NextAuth.js + JWT

**Status:** Accepted

**Context:** Need secure authentication for multi-user platform.

**Decision:** NextAuth.js with credentials provider, JWT tokens stored in HTTP-only cookies.

**Flow:**
1. User registers/logs in via `/api/auth/*`
2. Backend validates, returns JWT
3. NextAuth stores token in session
4. Frontend includes token in API requests
5. Backend validates JWT on protected routes

## ADR-010: Deployment Strategy

**Status:** Accepted

**Context:** Need production-ready deployment.

**Decision:**
- Frontend: Vercel (static + serverless)
- Backend: Railway/Render (container)
- Database: Neon/Managed PostgreSQL
- Cache: Redis Cloud/Upstash
- Storage: AWS S3 / Cloudflare R2
- Video: LiveKit Cloud
- CI/CD: GitHub Actions

**Rationale:**
- Managed services reduce ops burden
- Auto-scaling for interview load
- Free tiers for development
- Easy rollback/preview deployments