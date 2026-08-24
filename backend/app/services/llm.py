from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel
import json
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        pass
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        pass


class MockProvider(LLMProvider):
    """Mock LLM provider for testing without external API dependencies."""
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        # Return mock data based on the response model
        schema = response_model.model_json_schema()
        mock_data = self._get_mock_data(response_model.__name__)
        return response_model(**mock_data)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        # Return mock questions for interview generation
        if "SCREENING interview questions" in prompt or "screening" in prompt.lower():
            return json.dumps([
                {
                    "question_text": "I noticed you built a RAG-based chatbot using LangChain and Pinecone. Could you walk me through the retrieval pipeline you designed and how you optimized the chunking strategy for relevance?",
                    "question_type": "screening",
                    "expected_competencies": ["technical_knowledge", "communication", "problem_solving"],
                    "difficulty": "medium",
                    "generated_context": {
                        "resume_reference": "RAG-based chatbot project",
                        "evaluation_focus": "Technical depth in RAG systems, ability to articulate architecture decisions",
                        "ideal_answer_hints": "Should mention hybrid search, chunking strategy, evaluation framework",
                        "personalization": "Directly references the candidate's named RAG chatbot project"
                    }
                },
                {
                    "question_text": "You mentioned reducing API latency by 40% through Redis caching at TechCorp. What specific caching strategy did you implement, and how did you measure the improvement?",
                    "question_type": "screening",
                    "expected_competencies": ["technical_knowledge", "communication", "problem_solving"],
                    "difficulty": "easy",
                    "generated_context": {
                        "resume_reference": "Redis caching achievement at TechCorp",
                        "evaluation_focus": "Understanding of caching patterns, ability to quantify improvements",
                        "ideal_answer_hints": "Should mention cache invalidation, TTL, hit rates, before/after metrics",
                        "personalization": "References specific metric (40%) and company from resume"
                    }
                },
                {
                    "question_text": "The Senior Backend Engineer role requires experience with ML model serving and MLOps. Your ML Model Serving Platform project seems relevant. How did you handle A/B testing and monitoring in that platform?",
                    "question_type": "screening",
                    "expected_competencies": ["role_fit", "technical_knowledge", "communication"],
                    "difficulty": "medium",
                    "generated_context": {
                        "resume_reference": "ML Model Serving Platform project",
                        "evaluation_focus": "MLOps knowledge, system design for model serving",
                        "ideal_answer_hints": "Should mention A/B testing framework, Prometheus/Grafana monitoring, model versioning",
                        "personalization": "Connects candidate's project to JD requirement for MLOps"
                    }
                },
                {
                    "question_text": "What interests you most about this Senior Backend Engineer position, and how does it align with where you want to take your career?",
                    "question_type": "screening",
                    "expected_competencies": ["motivation", "career_goals", "role_fit"],
                    "difficulty": "easy",
                    "generated_context": {
                        "resume_reference": "Career trajectory from Backend to Senior Backend",
                        "evaluation_focus": "Motivation for this specific role, long-term alignment",
                        "ideal_answer_hints": "Should mention desire for system design, mentoring, ML integration",
                        "personalization": "References career progression shown in resume"
                    }
                },
                {
                    "question_text": "You've mentored 3 junior engineers who were promoted within a year. How do you approach mentorship, and what would you bring to our team culture?",
                    "question_type": "behavioral",
                    "expected_competencies": ["communication", "leadership", "behavioral_competencies"],
                    "difficulty": "easy",
                    "generated_context": {
                        "resume_reference": "Mentoring achievement at TechCorp",
                        "evaluation_focus": "Mentorship philosophy, cultural contribution",
                        "ideal_answer_hints": "Should mention specific mentorship practices, code reviews, knowledge sharing",
                        "personalization": "References specific achievement from resume"
                    }
                }
            ])
        elif "FOLLOW-UP" in prompt or "follow_up" in prompt.lower():
            return json.dumps({
                "question_text": "You mentioned using hybrid search with dense and sparse vectors. Why did you choose that approach over pure dense vector search, and what trade-offs did you consider?",
                "question_type": "follow_up",
                "expected_competencies": ["technical_depth", "reasoning", "decision_making"],
                "difficulty": "medium",
                "is_follow_up": True,
                "generated_context": {
                    "follow_up_reason": "Probe deeper into technical decision-making for retrieval architecture",
                    "targets_weakness": False,
                    "resume_reference": "RAG chatbot retrieval pipeline",
                    "evaluation_focus": "Understanding of search trade-offs, ability to justify architectural decisions"
                }
            })
        elif "COMPETENCY interview questions" in prompt or "level 2" in prompt.lower():
            return json.dumps([
                {
                    "question_text": "In your RAG chatbot, how did you handle the case where retrieved documents were irrelevant or contradictory? Walk me through your approach to handling edge cases in retrieval.",
                    "question_type": "technical",
                    "expected_competencies": ["problem_solving", "technical_depth", "edge_cases"],
                    "difficulty": "hard",
                    "generated_context": {
                        "resume_reference": "RAG chatbot project",
                        "evaluation_focus": "Edge case handling, retrieval quality assurance",
                        "ideal_answer_hints": "Should mention reranking, confidence thresholds, fallback strategies"
                    }
                }
            ])
        elif "DEEP-DIVE interview questions" in prompt or "level 3" in prompt.lower():
            return json.dumps([
                {
                    "question_text": "Design a system to serve multiple ML models with A/B testing, real-time monitoring, and automatic rollback on performance degradation. How would you architect this?",
                    "question_type": "deep_dive",
                    "expected_competencies": ["system_design", "technical_depth", "mlops"],
                    "difficulty": "hard",
                    "generated_context": {
                        "resume_reference": "ML Model Serving Platform project",
                        "evaluation_focus": "System design for ML serving, observability, reliability",
                        "ideal_answer_hints": "Should mention feature flags, canary deployment, metrics, alerting, rollback automation"
                    }
                }
            ])
        return "Mock response for: " + prompt[:100]
    
    def _get_mock_data(self, model_name: str) -> Dict[str, Any]:
        mocks = {
            "JDAnalysisResult": {
                "role_title": "Senior Backend Engineer",
                "responsibilities": [
                    "Design and implement scalable backend services",
                    "Optimize database queries and performance",
                    "Build and maintain CI/CD pipelines",
                    "Collaborate with ML engineers to serve models",
                    "Mentor junior engineers"
                ],
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
                "preferred_skills": ["MLOps", "GraphQL", "Celery", "LangChain", "Pinecone"],
                "technical_competencies": [
                    {"name": "Backend Development", "description": "Building scalable APIs and services", "importance": "high"},
                    {"name": "Database Design", "description": "PostgreSQL schema design and optimization", "importance": "high"},
                    {"name": "Caching", "description": "Redis caching strategies and invalidation", "importance": "high"},
                    {"name": "MLOps", "description": "ML model serving and monitoring", "importance": "medium"},
                    {"name": "System Design", "description": "Architecting scalable distributed systems", "importance": "high"}
                ],
                "behavioral_competencies": [
                    {"name": "Mentoring", "description": "Guiding and developing junior engineers", "importance": "high"},
                    {"name": "Collaboration", "description": "Working cross-functionally with ML engineers", "importance": "high"},
                    {"name": "Problem Solving", "description": "Debugging and optimizing complex systems", "importance": "high"}
                ],
                "experience_expectations": "5+ years of backend engineering experience",
                "keywords": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes", "MLOps", "GraphQL"],
                "concepts": ["RAG", "MLOps", "Caching", "Microservices", "CI/CD", "A/B Testing"],
                "qualifications": ["Bachelor's in Computer Science or equivalent experience"]
            },
            "ResumeAnalysisResult": {
                "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Celery", "Docker", "Kubernetes", "LangChain", "Pinecone", "OpenAI", "GraphQL", "GitHub Actions"],
                "experience": [
                    {"role": "Senior Backend Engineer", "company": "TechCorp", "duration": "2021-Present", "description": "Built scalable APIs using Python/FastAPI handling 1M+ requests/day. Designed PostgreSQL schemas for multi-tenant SaaS platform. Implemented Redis caching layer reducing latency by 40%. Set up CI/CD pipelines with GitHub Actions and Docker. Mentored 3 junior engineers."},
                    {"role": "Backend Engineer", "company": "StartupXYZ", "duration": "2019-2021", "description": "Developed REST APIs using Python/Flask. Worked with PostgreSQL and MongoDB. Built async task processing with Celery and Redis."}
                ],
                "projects": [
                    {"name": "RAG-based Chatbot", "description": "Built a retrieval-augmented generation chatbot using LangChain, Pinecone, and OpenAI. Solved the problem of hallucination in customer support by grounding responses in documentation.", "technologies": ["Python", "LangChain", "Pinecone", "OpenAI", "FastAPI"], "impact": "Serving 10k+ queries/month with 95% accuracy"},
                    {"name": "ML Model Serving Platform", "description": "Built a platform to serve ML models with A/B testing and monitoring.", "technologies": ["Python", "FastAPI", "Docker", "Kubernetes", "Prometheus", "Grafana"], "impact": "Enabled safe model deployment with automated rollback"}
                ],
                "achievements": [
                    "Reduced API latency by 40% through Redis caching",
                    "Built RAG chatbot serving 10k+ queries/month with 95% accuracy",
                    "Mentored 3 engineers who were promoted within 1 year"
                ],
                "strengths": [
                    "Strong Python/FastAPI expertise",
                    "Production PostgreSQL and Redis experience",
                    "MLOps and model serving experience",
                    "RAG system implementation",
                    "Mentoring and team leadership"
                ],
                "missing_skills": ["GraphQL (limited)", "Advanced Kubernetes (basics only)"],
                "weak_areas": [
                    {"area": "GraphQL", "reason": "Mentioned but no production project listed"},
                    {"area": "Advanced Kubernetes", "reason": "Only basic Docker/K8s experience mentioned"}
                ],
                "questionable_claims": [
                    {"claim": "1M+ requests/day", "why_questionable": "No supporting metrics or architecture details provided", "follow_up_questions": ["What was the peak QPS?", "What infrastructure handled this load?"]},
                    {"claim": "95% accuracy on RAG chatbot", "why_questionable": "Accuracy metric needs clarification - retrieval accuracy or end-to-end?", "follow_up_questions": ["How was accuracy measured?", "What was the evaluation dataset?"]}
                ]
            },
            "JobFitAnalysisResult": {
                "score": 78,
                "rating": "Good Match",
                "strong_matches": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "MLOps", "Mentoring"],
                "partial_matches": ["Kubernetes", "Celery", "System Design", "GraphQL"],
                "missing_weak": ["Advanced Kubernetes", "Production GraphQL"],
                "methodology": "4-Pillar Evaluation: Required Core Skills (40%), Experience & Domain Fit (30%), Preferred Skills (15%), Gaps Analysis (15%).",
                "skill_match_details": {
                    "required_match_pct": 83,
                    "preferred_match_pct": 60,
                    "total_required": 6,
                    "total_preferred": 5,
                    "matched_required": 5,
                    "matched_preferred": 3
                }
            }
        }
        return mocks.get(model_name, {})


class NemotronProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.NEMOTRON_API_BASE
        self.api_key = settings.NEMOTRON_API_KEY
        self.model = settings.NEMOTRON_MODEL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=120.0,
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        schema = response_model.model_json_schema()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        structured_prompt = f"""{prompt}

You must respond with a valid JSON object that matches this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text."""
        
        messages.append({"role": "user", "content": structured_prompt})
        
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        try:
            parsed = json.loads(content)
            return response_model(**parsed)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON", error=str(e), content=content[:500])
            raise
        except Exception as e:
            logger.error("Failed to validate LLM response", error=str(e))
            raise
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def close(self):
        await self.client.aclose()


class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_model,
        )
        return response.choices[0].message.parsed
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    def __init__(self):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        schema = response_model.model_json_schema()
        
        system = system_prompt or ""
        system += f"\n\nYou must respond with a valid JSON object matching this schema:\n{json.dumps(schema, indent=2)}"
        
        response = await self.client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.content[0].text
        parsed = json.loads(content)
        return response_model(**parsed)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text


class LLMService:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        # Always add mock provider as fallback
        self.providers["mock"] = MockProvider()
        
        if settings.NEMOTRON_API_BASE:
            self.providers["nemotron"] = NemotronProvider()
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider()
        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider()
        
        # Prefer mock for development, then nemotron, then openai, then anthropic
        self.provider_order = [p for p in ["mock", "nemotron", "openai", "anthropic"] if p in self.providers]
        self.default_provider = self.provider_order[0] if self.provider_order else None
    
    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        provider_name = name or self.default_provider
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"LLM provider '{provider_name}' not available")
        return self.providers[provider_name]
    
    async def _try_providers(self, func_name: str, *args, **kwargs) -> Any:
        """Try providers in order until one succeeds."""
        last_error = None
        for provider_name in self.provider_order:
            try:
                provider = self.providers[provider_name]
                method = getattr(provider, func_name)
                return await method(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed", error=str(e))
                last_error = e
                continue
        raise last_error or RuntimeError("All providers failed")
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> T:
        if provider:
            llm = self.get_provider(provider)
            return await llm.generate_structured(prompt, response_model, system_prompt, **kwargs)
        return await self._try_providers("generate_structured", prompt, response_model, system_prompt, **kwargs)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> str:
        if provider:
            llm = self.get_provider(provider)
            return await llm.generate_text(prompt, system_prompt, **kwargs)
        return await self._try_providers("generate_text", prompt, system_prompt, **kwargs)
    
    async def close(self):
        for provider in self.providers.values():
            if hasattr(provider, "close"):
                await provider.close()


llm_service = LLMService()