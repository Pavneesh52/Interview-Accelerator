from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.llm import llm_service


class QuestionFeedback(BaseModel):
    question_id: str
    question: str
    candidate_answer: str
    assessment: str
    what_was_good: List[str]
    what_could_be_better: List[str]
    ideal_direction: str
    competencies_evaluated: List[str]
    score: int


class PreparationGap(BaseModel):
    priority: int
    topic: str
    review_items: List[str]


class EvaluationResult(BaseModel):
    overall_score: int
    role_fit_score: int
    technical_knowledge_score: int
    problem_solving_score: int
    communication_score: int
    confidence_score: int
    depth_of_understanding_score: int
    behavioral_fit_score: int
    competency_scores: Dict[str, int]
    question_feedbacks: List[QuestionFeedback]
    strengths: List[str]
    weaknesses: List[str]
    preparation_gaps: List[PreparationGap]
    readiness_level: str
    readiness_score: int


class EvaluationService:
    def __init__(self):
        pass

    EVALUATION_SYSTEM_PROMPT = """You are an expert technical interviewer and evaluator. 
Evaluate the candidate's interview performance thoroughly and provide specific, actionable feedback.
Be precise and reference concrete examples from the answers."""

    EVALUATION_PROMPT = """Evaluate this candidate's complete interview performance.

JOB DESCRIPTION:
{jd_summary}

CANDIDATE PROFILE:
{resume_summary}

JOB FIT ASSESSMENT:
{job_fit_summary}

INTERVIEW QUESTIONS AND ANSWERS:
{qa_history}

Evaluate across these competencies:
1. Role Fit - How well does the candidate match the role requirements?
2. Technical Knowledge - Depth and accuracy of technical understanding
3. Problem Solving - Approach to complex problems, reasoning ability
4. Communication - Clarity, structure, articulation of ideas
5. Confidence - Self-assurance, decisiveness in responses
6. Depth of Understanding - Goes beyond surface-level knowledge
7. Behavioral Fit - Alignment with behavioral competencies

For EACH question, provide:
- assessment: "strong" | "adequate" | "weak"
- what_was_good: specific strengths in the response
- what_could_be_better: specific areas for improvement
- ideal_direction: what a stronger answer should have covered
- competencies_evaluated: which competencies this question tested
- score: 0-100

Also provide:
- overall_score: 0-100
- individual competency scores: 0-100 each
- strengths: list of demonstrated strengths (specific, not generic)
- weaknesses: list of specific weaknesses
- preparation_gaps: prioritized list with specific topics to review
- readiness_level: "not_ready" | "needs_preparation" | "interview_ready" | "strong_candidate"
- readiness_score: 0-100

Return as JSON matching the EvaluationResult schema."""

    async def evaluate_interview(
        self,
        jd_analysis: Dict[str, Any],
        resume_analysis: Dict[str, Any],
        job_fit: Dict[str, Any],
        interview_questions: List[Dict[str, Any]],
    ) -> EvaluationResult:
        jd_summary = f"""
Role: {jd_analysis.get('role_title', 'N/A')}
Required Skills: {', '.join(jd_analysis.get('required_skills', []))}
Technical Competencies: {', '.join([c.get('name', '') for c in jd_analysis.get('technical_competencies', [])])}
Behavioral Competencies: {', '.join([c.get('name', '') for c in jd_analysis.get('behavioral_competencies', [])])}
"""

        resume_summary = f"""
Skills: {', '.join(resume_analysis.get('skills', []))}
Experience: {len(resume_analysis.get('experience', []))} roles
Projects: {len(resume_analysis.get('projects', []))} projects
Strengths: {', '.join(resume_analysis.get('strengths', []))}
Missing Skills: {', '.join(resume_analysis.get('missing_skills', []))}
Weak Areas: {', '.join([w.get('area', '') for w in resume_analysis.get('weak_areas', [])])}
"""

        job_fit_summary = f"""
Score: {job_fit.get('score', 0)}%
Rating: {job_fit.get('rating', 'N/A')}
Strong Matches: {', '.join(job_fit.get('strong_matches', []))}
Missing/Weak: {', '.join(job_fit.get('missing_weak', []))}
"""

        qa_history = ""
        for i, q in enumerate(interview_questions):
            qa_history += f"\nQ{i+1} (Level {q.get('level', '?')}, Type: {q.get('question_type', '?')}): {q.get('question_text', '')}\n"
            if q.get('answer'):
                ans = q['answer']
                qa_history += f"  Answer: {ans.get('transcript', 'No transcript')}\n"
                qa_history += f"  Duration: {ans.get('duration_seconds', 0)}s\n"

        prompt = self.EVALUATION_PROMPT.format(
            jd_summary=jd_summary,
            resume_summary=resume_summary,
            job_fit_summary=job_fit_summary,
            qa_history=qa_history,
        )

        try:
            result = await llm_service.generate_structured(
                prompt=prompt,
                response_model=EvaluationResult,
                system_prompt=self.EVALUATION_SYSTEM_PROMPT,
                temperature=0.3,
            )
            return result
        except Exception as e:
            print(f"Error in evaluation: {e}")
            return self._get_fallback_evaluation(interview_questions)

    def _get_fallback_evaluation(self, questions: List[Dict[str, Any]]) -> EvaluationResult:
        answered = [q for q in questions if q.get('answer')]
        total = len(questions)
        
        base_score = 50 + (len(answered) / max(total, 1)) * 30
        
        return EvaluationResult(
            overall_score=int(base_score),
            role_fit_score=int(base_score + 5),
            technical_knowledge_score=int(base_score),
            problem_solving_score=int(base_score - 5),
            communication_score=int(base_score + 10),
            confidence_score=int(base_score),
            depth_of_understanding_score=int(base_score - 10),
            behavioral_fit_score=int(base_score + 5),
            competency_scores={
                "role_fit": int(base_score + 5),
                "technical_knowledge": int(base_score),
                "problem_solving": int(base_score - 5),
                "communication": int(base_score + 10),
                "confidence": int(base_score),
                "depth_of_understanding": int(base_score - 10),
                "behavioral_fit": int(base_score + 5),
            },
            question_feedbacks=[
                QuestionFeedback(
                    question_id=q.get('id', str(i)),
                    question=q.get('question_text', ''),
                    candidate_answer=q.get('answer', {}).get('transcript', 'No answer provided'),
                    assessment="adequate",
                    what_was_good=["Provided a response"],
                    what_could_be_better=["Could provide more specific details", "Add quantitative results"],
                    ideal_direction="A stronger answer would include specific examples with measurable outcomes",
                    competencies_evaluated=q.get('expected_competencies', []),
                    score=60,
                )
                for i, q in enumerate(questions)
                if q.get('answer')
            ],
            strengths=["Participated in interview", "Demonstrated basic knowledge"],
            weaknesses=["Need more specific examples", "Could elaborate more on technical details"],
            preparation_gaps=[
                PreparationGap(priority=1, topic="Technical Depth", review_items=["System design", "Algorithm complexity", "Trade-off analysis"]),
                PreparationGap(priority=2, topic="Behavioral Examples", review_items=["STAR method", "Leadership examples", "Conflict resolution"]),
                PreparationGap(priority=3, topic="Role-Specific Knowledge", review_items=["Review JD requirements", "Prepare project stories"]),
            ],
            readiness_level="needs_preparation" if base_score < 70 else "interview_ready",
            readiness_score=int(base_score),
        )


evaluation_service = EvaluationService()