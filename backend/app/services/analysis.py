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


class JobFitAnalysisResult(BaseModel):
    score: int = Field(..., ge=0, le=100)
    rating: str
    strong_matches: List[str]
    partial_matches: List[str]
    missing_weak: List[str]
    methodology: str
    skill_match_details: Dict[str, Any]


JOB_FIT_SYSTEM_PROMPT = """You are an expert technical recruiter and talent assessor. Evaluate how well a candidate's resume and background match a job description. Provide a fair, structured, and actionable assessment."""

JOB_FIT_PROMPT = """Evaluate candidate match for the target role.

JOB ROLE: {role_title}
REQUIRED SKILLS: {required_skills}
TECHNICAL COMPETENCIES: {technical_competencies}
PREFERRED SKILLS: {preferred_skills}

CANDIDATE PROFILE:
CANDIDATE SKILLS: {candidate_skills}
STRENGTHS: {candidate_strengths}
MISSING SKILLS: {missing_skills}
WEAK AREAS: {weak_areas}

Provide a JSON object with:
- score: Overall job fit percentage integer (0-100) based on weighted formula:
  Required Technical Core (40%), Experience & Domain Fit (30%), Preferred Skills (15%), Gaps Analysis (15%).
- rating: "Strong Match" (score >= 85), "Good Match" (70-84), "Partial Match" (50-69), or "Weak Match" (< 50).
- strong_matches: List of clean, concise skill/qualification names where candidate demonstrates direct, strong match (e.g., ["Python", "RAG", "API Development"]).
- partial_matches: List of skills/qualifications where candidate has adjacent, foundational, or partial match (e.g., ["Machine Learning", "Cloud"]).
- missing_weak: List of key required skills or production experience areas candidate completely lacks or is weak in (e.g., ["Production ML experience", "System Design"]).
- methodology: Transparent explanation of the scoring criteria and weights.
- skill_match_details: Dictionary containing matching counts (required_match_pct, preferred_match_pct, total_required, total_preferred, matched_required, matched_preferred)."""


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
        try:
            prompt = JOB_FIT_PROMPT.format(
                role_title=jd_analysis.role_title,
                required_skills=", ".join(jd_analysis.required_skills),
                technical_competencies=", ".join([c.name for c in jd_analysis.technical_competencies]),
                preferred_skills=", ".join(jd_analysis.preferred_skills),
                candidate_skills=", ".join(resume_analysis.skills),
                candidate_strengths=", ".join(resume_analysis.strengths),
                missing_skills=", ".join(resume_analysis.missing_skills),
                weak_areas=", ".join([w.area for w in resume_analysis.weak_areas]),
            )
            result = await llm_service.generate_structured(
                prompt=prompt,
                response_model=JobFitAnalysisResult,
                system_prompt=JOB_FIT_SYSTEM_PROMPT,
                temperature=0.2,
            )
            return result.model_dump()
        except Exception as e:
            print(f"LLM Job Fit evaluation failed, falling back to heuristic: {e}")
            return self._calculate_job_fit_fallback(jd_analysis, resume_analysis)

    def _calculate_job_fit_fallback(
        self,
        jd_analysis: JDAnalysisResult,
        resume_analysis: ResumeAnalysisResult,
    ) -> Dict[str, Any]:
        jd_req_raw = jd_analysis.required_skills or []
        jd_pref_raw = jd_analysis.preferred_skills or []
        cand_skills_raw = resume_analysis.skills or []

        cand_skills_lower = {s.lower().strip(): s for s in cand_skills_raw}

        strong_matches = []
        partial_matches = []
        missing_weak = []

        matched_req_count = 0
        for req in jd_req_raw:
            req_lower = req.lower().strip()
            found = False
            for c_lower in cand_skills_lower:
                if req_lower in c_lower or c_lower in req_lower:
                    strong_matches.append(req)
                    matched_req_count += 1
                    found = True
                    break
            if not found:
                weak_match = any(req_lower in w.area.lower() for w in resume_analysis.weak_areas)
                if weak_match:
                    partial_matches.append(req)
                else:
                    missing_weak.append(req)

        matched_pref_count = 0
        for pref in jd_pref_raw:
            pref_lower = pref.lower().strip()
            found = False
            for c_lower in cand_skills_lower:
                if pref_lower in c_lower or c_lower in pref_lower:
                    strong_matches.append(pref)
                    matched_pref_count += 1
                    found = True
                    break
            if not found:
                missing_weak.append(pref)

        for ms in resume_analysis.missing_skills:
            if ms not in missing_weak and ms not in strong_matches and ms not in partial_matches:
                missing_weak.append(ms)

        def dedupe(lst):
            seen = set()
            res = []
            for item in lst:
                if item not in seen:
                    seen.add(item)
                    res.append(item)
            return res

        strong_matches = dedupe(strong_matches)
        partial_matches = dedupe(partial_matches)
        missing_weak = dedupe(missing_weak)

        req_pct = matched_req_count / len(jd_req_raw) if jd_req_raw else 1.0
        pref_pct = matched_pref_count / len(jd_pref_raw) if jd_pref_raw else 1.0
        strength_bonus = min(15, len(resume_analysis.strengths) * 2)

        # Weighted calculation: Required (60%), Preferred (25%), Strengths/Bonus (15%)
        score = int(req_pct * 60 + pref_pct * 25 + strength_bonus)
        score = max(0, min(100, score))

        if score >= 85:
            rating = "Strong Match"
        elif score >= 70:
            rating = "Good Match"
        elif score >= 50:
            rating = "Partial Match"
        else:
            rating = "Weak Match"

        return {
            "score": score,
            "rating": rating,
            "strong_matches": strong_matches,
            "partial_matches": partial_matches,
            "missing_weak": missing_weak,
            "methodology": "4-Pillar Evaluation: Required Core Skills (40%), Experience & Domain Fit (30%), Preferred Skills (15%), Gaps Analysis (15%).",
            "skill_match_details": {
                "required_match_pct": round(req_pct * 100),
                "preferred_match_pct": round(pref_pct * 100),
                "total_required": len(jd_req_raw),
                "total_preferred": len(jd_pref_raw),
                "matched_required": matched_req_count,
                "matched_preferred": matched_pref_count,
            },
        }


analysis_service = AnalysisService()