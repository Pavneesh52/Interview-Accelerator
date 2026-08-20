from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.services.llm import llm_service


class TechnicalCompetency(BaseModel):
    name: str
    description: str
    importance: str


class BehavioralCompetency(BaseModel):
    name: str
    description: str
    importance: str


class JDAnalysisResult(BaseModel):
    role_title: str
    responsibilities: List[str]
    required_skills: List[str]
    preferred_skills: List[str]
    technical_competencies: List[TechnicalCompetency]
    behavioral_competencies: List[BehavioralCompetency]
    experience_expectations: str
    keywords: List[str]
    concepts: List[str]
    qualifications: List[str]


class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: str
    description: str


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str]
    impact: str


class WeakArea(BaseModel):
    area: str
    reason: str


class QuestionableClaim(BaseModel):
    claim: str
    why_questionable: str
    follow_up_questions: List[str]


class ResumeAnalysisResult(BaseModel):
    skills: List[str]
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    achievements: List[str]
    strengths: List[str]
    missing_skills: List[str]
    weak_areas: List[WeakArea]
    questionable_claims: List[QuestionableClaim]


JD_ANALYSIS_SYSTEM_PROMPT = """You are an expert technical recruiter and hiring manager. Analyze the job description thoroughly and extract structured information. Be specific and detailed - this will be used to create personalized interview questions."""

JD_ANALYSIS_PROMPT = """Analyze this Job Description and extract the following information:

JOB DESCRIPTION:
{jd_text}

Return a JSON object with:
- role_title: The exact job title/role
- responsibilities: List of key responsibilities (5-10 items)
- required_skills: List of required technical skills (explicitly mentioned)
- preferred_skills: List of preferred/nice-to-have skills
- technical_competencies: List of objects with name, description, importance (high/medium/low)
- behavioral_competencies: List of objects with name, description, importance (high/medium/low)
- experience_expectations: Description of years/type of experience expected
- keywords: Important keywords from the JD (10-20)
- concepts: Key concepts/technologies mentioned (10-15)
- qualifications: Required qualifications (degrees, certifications, etc.)"""

RESUME_ANALYSIS_SYSTEM_PROMPT = """You are an expert technical recruiter analyzing a candidate's resume against a specific job description. Extract structured information that will be used for job fit assessment and personalized interview generation. Be thorough and honest about gaps."""

RESUME_ANALYSIS_PROMPT = """Analyze this candidate's resume in the context of the job description.

JOB DESCRIPTION ANALYSIS:
{jd_analysis}

CANDIDATE RESUME:
{resume_text}

Return a JSON object with:
- skills: All technical skills mentioned in resume (list)
- experience: List of work experience with role, company, duration, description
- projects: List of projects with name, description, technologies, impact
- achievements: Quantifiable achievements and accomplishments
- strengths: Strengths specifically relevant to the JD (5-10)
- missing_skills: Skills required by JD but not found in resume
- weak_areas: Areas where candidate has some experience but insufficient for JD (list of objects with area and reason)
- questionable_claims: Claims in resume that need verification during interview (list of objects with claim, why_questionable, follow_up_questions)"""


class AnalysisService:
    def __init__(self):
        pass
    
    async def analyze_jd(self, jd_text: str) -> JDAnalysisResult:
        result = await llm_service.generate_structured(
            prompt=JD_ANALYSIS_PROMPT.format(jd_text=jd_text),
            response_model=JDAnalysisResult,
            system_prompt=JD_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2,
        )
        return result
    
    async def analyze_resume(self, resume_text: str, jd_analysis: JDAnalysisResult) -> ResumeAnalysisResult:
        jd_summary = f"""
Role: {jd_analysis.role_title}
Required Skills: {', '.join(jd_analysis.required_skills)}
Preferred Skills: {', '.join(jd_analysis.preferred_skills)}
Technical Competencies: {', '.join([c.name for c in jd_analysis.technical_competencies])}
Behavioral Competencies: {', '.join([c.name for c in jd_analysis.behavioral_competencies])}
Experience: {jd_analysis.experience_expectations}
Keywords: {', '.join(jd_analysis.keywords)}
"""
        
        result = await llm_service.generate_structured(
            prompt=RESUME_ANALYSIS_PROMPT.format(
                jd_analysis=jd_summary,
                resume_text=resume_text,
            ),
            response_model=ResumeAnalysisResult,
            system_prompt=RESUME_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2,
        )
        return result
    
    async def calculate_job_fit(
        self,
        jd_analysis: JDAnalysisResult,
        resume_analysis: ResumeAnalysisResult,
    ) -> Dict[str, Any]:
        # Skill matching
        jd_required = set(s.lower() for s in jd_analysis.required_skills)
        jd_preferred = set(s.lower() for s in jd_analysis.preferred_skills)
        candidate_skills = set(s.lower() for s in resume_analysis.skills)
        
        required_matches = jd_required & candidate_skills
        preferred_matches = jd_preferred & candidate_skills
        missing_required = jd_required - candidate_skills
        missing_preferred = jd_preferred - candidate_skills
        
        required_match_pct = len(required_matches) / len(jd_required) if jd_required else 1.0
        preferred_match_pct = len(preferred_matches) / len(jd_preferred) if jd_preferred else 1.0
        
        # Weighted score
        score = int(
            required_match_pct * 50 +
            preferred_match_pct * 20 +
            (1 - len(resume_analysis.missing_skills) / max(len(jd_analysis.required_skills), 1)) * 15 +
            (len(resume_analysis.strengths) / 10) * 15
        )
        score = max(0, min(100, score))
        
        if score >= 80:
            rating = "Strong Match"
        elif score >= 60:
            rating = "Good Match"
        elif score >= 40:
            rating = "Partial Match"
        else:
            rating = "Weak Match"
        
        return {
            "score": score,
            "rating": rating,
            "strong_matches": list(required_matches) + list(preferred_matches),
            "partial_matches": list(candidate_skills & (jd_required | jd_preferred) - required_matches - preferred_matches),
            "missing_weak": list(missing_required) + list(missing_preferred) + resume_analysis.missing_skills,
            "methodology": "Weighted: Required Skills (50%), Preferred Skills (20%), Experience Relevance (15%), Strengths (15%)",
            "skill_match_details": {
                "required_match_pct": round(required_match_pct * 100),
                "preferred_match_pct": round(preferred_match_pct * 100),
                "total_required": len(jd_required),
                "total_preferred": len(jd_preferred),
                "matched_required": len(required_matches),
                "matched_preferred": len(preferred_matches),
            },
        }


analysis_service = AnalysisService()