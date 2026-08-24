#!/usr/bin/env python3
"""Test the full interview flow: JD + Resume -> Analysis -> Interview"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

JD_TEXT = """We are looking for a Senior Backend Engineer to join our team. The ideal candidate will have:
- 5+ years of experience with Python and FastAPI
- Strong experience with PostgreSQL and database design
- Experience with Redis, Celery, and async programming
- Knowledge of Docker and Kubernetes
- Experience with ML model serving and MLOps
- Strong system design skills
- Experience with REST APIs and GraphQL

Responsibilities:
- Design and implement scalable backend services
- Optimize database queries and performance
- Build and maintain CI/CD pipelines
- Collaborate with ML engineers to serve models
- Mentor junior engineers"""

RESUME_TEXT = """John Doe
Senior Backend Engineer

EXPERIENCE:
- Senior Backend Engineer at TechCorp (2021-Present)
  - Built scalable APIs using Python/FastAPI handling 1M+ requests/day
  - Designed PostgreSQL schemas for multi-tenant SaaS platform
  - Implemented Redis caching layer reducing latency by 40%
  - Set up CI/CD pipelines with GitHub Actions and Docker
  - Mentored 3 junior engineers

- Backend Engineer at StartupXYZ (2019-2021)
  - Developed REST APIs using Python/Flask
  - Worked with PostgreSQL and MongoDB
  - Built async task processing with Celery and Redis

PROJECTS:
- RAG-based Chatbot (2023)
  - Built a retrieval-augmented generation chatbot using LangChain, Pinecone, and OpenAI
  - Solved the problem of hallucination in customer support by grounding responses in documentation
  - My contribution: Designed the retrieval pipeline, implemented hybrid search, optimized chunking strategy
  - Technologies: Python, LangChain, Pinecone, OpenAI, FastAPI

- ML Model Serving Platform (2022)
  - Built a platform to serve ML models with A/B testing and monitoring
  - Technologies: Python, FastAPI, Docker, Kubernetes, Prometheus, Grafana

SKILLS:
Python, FastAPI, PostgreSQL, Redis, Celery, Docker, Kubernetes, LangChain, Pinecone, OpenAI, GraphQL, GitHub Actions

ACHIEVEMENTS:
- Reduced API latency by 40% through Redis caching
- Built RAG chatbot serving 10k+ queries/month with 95% accuracy
- Mentored 3 engineers who were promoted within 1 year"""

async def test_full_flow():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Register/Login
        print("=== Step 1: Register user ===")
        resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": "test_flow@example.com",
            "password": "testpassword123",
            "full_name": "Test Flow User"
        })
        if resp.status_code == 400:
            print("User exists, logging in...")
        else:
            print(f"User registered: {resp.json()['id']}")
        
        # Login to get token
        resp = await client.post(f"{BASE_URL}/auth/login", 
            json={"email": "test_flow@example.com", "password": "testpassword123"})
        token_data = resp.json()
        token = token_data.get("access_token")
        if not token:
            print(f"Failed to get token: {token_data}")
            return
        print(f"Got token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Upload JD
        print("\n=== Step 2: Upload JD ===")
        resp = await client.post(f"{BASE_URL}/documents/jd/paste", 
            json={"title": "Senior Backend Engineer", "raw_text": JD_TEXT},
            headers=headers)
        jd = resp.json()
        jd_id = jd["id"]
        print(f"JD created: {jd_id}")
        
        # 3. Upload Resume
        print("\n=== Step 3: Upload Resume ===")
        resp = await client.post(f"{BASE_URL}/documents/resume/paste",
            json={"raw_text": RESUME_TEXT},
            headers=headers)
        resume = resp.json()
        resume_id = resume["id"]
        print(f"Resume created: {resume_id}")
        
        # 4. Create analysis session
        print("\n=== Step 4: Create analysis session ===")
        resp = await client.post(f"{BASE_URL}/analysis/sessions",
            json={"jd_id": jd_id, "resume_id": resume_id},
            headers=headers)
        session = resp.json()
        session_id = session["id"]
        print(f"Session created: {session_id}")
        
        # 5. Run analysis
        print("\n=== Step 5: Run analysis ===")
        resp = await client.post(f"{BASE_URL}/analysis/sessions/{session_id}/analyze", headers=headers)
        print(f"Analysis started: {resp.json()}")
        
        # Poll for completion
        for i in range(30):
            await asyncio.sleep(3)
            resp = await client.get(f"{BASE_URL}/analysis/sessions/{session_id}", headers=headers)
            session_data = resp.json()
            print(f"  Poll {i+1}: status = {session_data['status']}")
            if session_data["status"] == "completed":
                print("Analysis completed!")
                break
            elif session_data["status"] == "failed":
                print("Analysis failed!")
                return
        else:
            print("Timeout waiting for analysis")
            return
        
        # 6. Check job fit
        print("\n=== Step 6: Check job fit ===")
        resp = await client.get(f"{BASE_URL}/analysis/sessions/{session_id}/job-fit", headers=headers)
        job_fit = resp.json()
        print(f"Job Fit Score: {job_fit['score']}% ({job_fit['rating']})")
        print(f"Strong matches: {job_fit['strong_matches']}")
        print(f"Missing/weak: {job_fit['missing_weak']}")
        
        # 7. Start interview
        print("\n=== Step 7: Start interview ===")
        resp = await client.post(f"{BASE_URL}/interviews/interviews/start",
            json={"session_id": session_id},
            headers=headers)
        interview = resp.json()
        interview_id = interview["id"]
        print(f"Interview started: {interview_id}")
        print(f"Status: {interview['status']}")
        print(f"Current level: {interview['current_level']}")
        print(f"Total questions: {interview['total_questions']}")
        
        # 8. Get interviewer intro
        print("\n=== Step 8: Get interviewer intro ===")
        resp = await client.get(f"{BASE_URL}/interviews/interviews/{interview_id}/intro", headers=headers)
        intro = resp.json()
        print(f"Greeting: {intro['greeting'][:200]}...")
        print(f"Focus areas: {intro['focus_areas']}")
        
        # 9. Get first question
        print("\n=== Step 9: Get first question ===")
        resp = await client.get(f"{BASE_URL}/interviews/interviews/{interview_id}/current-question", headers=headers)
        current = resp.json()
        q = current["question"]
        print(f"Question: {q['question_text']}")
        print(f"Type: {q['question_type']}")
        print(f"Difficulty: {q['difficulty']}")
        print(f"Expected competencies: {q['expected_competencies']}")
        print(f"Progress: {current['progress']}%")
        
        # 10. Submit answer
        print("\n=== Step 10: Submit answer ===")
        answer_text = "I worked on a RAG-based chatbot where I designed the retrieval pipeline using LangChain and Pinecone. The problem was that our customer support bot was hallucinating answers. My solution was to implement a hybrid search combining dense and sparse vectors, and I optimized the chunking strategy to improve relevance. I specifically contributed the retrieval architecture and the evaluation framework."
        resp = await client.post(f"{BASE_URL}/interviews/interviews/questions/{q['id']}/answer",
            json={"transcript": answer_text, "duration_seconds": 60},
            headers=headers)
        print(f"Answer submitted: status={resp.status_code}, body={resp.text}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return
        try:
            answer_data = resp.json()
            print(f"Answer data: {answer_data}")
        except:
            print("No JSON in response")
        
        # 11. Get next question
        print("\n=== Step 11: Get next question ===")
        resp = await client.post(f"{BASE_URL}/interviews/interviews/{interview_id}/next-question", headers=headers)
        print(f"Next question response: status={resp.status_code}, body={resp.text}")
        if resp.status_code == 200:
            next_q = resp.json()
            print(f"Next question: {next_q['question_text']}")
            print(f"Is follow-up: {next_q['is_follow_up']}")
            if next_q.get('is_follow_up'):
                print(f"Parent question ID: {next_q['parent_question_id']}")
                print(f"Follow-up context: {next_q.get('generated_context', {})}")
        else:
            print(f"Error getting next question: {resp.text}")
        
        print("\n=== FLOW TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_full_flow())