from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.llm import llm_service


class QuestionContext(BaseModel):
    jd_analysis: Dict[str, Any]
    resume_analysis: Dict[str, Any]
    job_fit: Dict[str, Any]
    interview_history: List[Dict[str, Any]]
    current_level: int
    difficulty_adjustment: float
    topics_covered: List[str]
    weaknesses_identified: List[str]
    strengths_confirmed: List[str]


class GeneratedQuestion(BaseModel):
    question_text: str
    question_type: str
    expected_competencies: List[str]
    difficulty: str
    is_follow_up: bool = False
    parent_question_id: Optional[str] = None
    generated_context: Dict[str, Any] = {}


class InterviewService:
    def __init__(self):
        pass

    LEVEL_CONFIG = {
        1: {
            "name": "Screening",
            "num_questions": 5,
            "focus": ["resume", "motivation", "basic_understanding", "role_fit", "communication"],
            "question_types": ["screening", "behavioral"],
            "difficulty_range": ["easy", "medium"],
        },
        2: {
            "name": "Competency",
            "num_questions": 7,
            "focus": ["technical_knowledge", "problem_solving", "projects", "behavioral_competencies", "decision_making"],
            "question_types": ["technical", "behavioral", "scenario"],
            "difficulty_range": ["medium", "hard"],
        },
        3: {
            "name": "Deep-Dive",
            "num_questions": 10,
            "focus": ["technical_depth", "reasoning", "edge_cases", "trade_offs", "challenges", "inconsistencies"],
            "question_types": ["deep_dive", "scenario", "follow_up"],
            "difficulty_range": ["hard"],
        },
    }

    def build_context(self, session_data: Dict[str, Any], interview_state: Dict[str, Any]) -> QuestionContext:
        return QuestionContext(
            jd_analysis=session_data.get("jd_analysis", {}),
            resume_analysis=session_data.get("resume_analysis", {}),
            job_fit=session_data.get("job_fit", {}),
            interview_history=interview_state.get("questions", []),
            current_level=interview_state.get("current_level", 1),
            difficulty_adjustment=interview_state.get("difficulty_adjustment", 0.0),
            topics_covered=interview_state.get("topics_covered", []),
            weaknesses_identified=interview_state.get("weaknesses_identified", []),
            strengths_confirmed=interview_state.get("strengths_confirmed", []),
        )

    def _get_level_prompt(self, level: int, context: QuestionContext, is_follow_up: bool = False) -> str:
        level_config = self.LEVEL_CONFIG[level]
        
        jd = context.jd_analysis
        resume = context.resume_analysis
        job_fit = context.job_fit
        history = context.interview_history
        
        jd_summary = f"""
JOB DESCRIPTION ANALYSIS:
- Role: {jd.get('role_title', 'N/A')}
- Required Skills: {', '.join(jd.get('required_skills', []))}
- Preferred Skills: {', '.join(jd.get('preferred_skills', []))}
- Technical Competencies: {', '.join([c.get('name', '') for c in jd.get('technical_competencies', [])])}
- Behavioral Competencies: {', '.join([c.get('name', '') for c in jd.get('behavioral_competencies', [])])}
- Experience Expectations: {jd.get('experience_expectations', 'N/A')}
- Keywords: {', '.join(jd.get('keywords', []))}
"""
        
        resume_summary = f"""
CANDIDATE RESUME ANALYSIS:
- Skills: {', '.join(resume.get('skills', []))}
- Experience: {len(resume.get('experience', []))} roles
- Projects: {len(resume.get('projects', []))} projects
- Achievements: {', '.join(resume.get('achievements', [])[:3])}
- Strengths: {', '.join(resume.get('strengths', []))}
- Missing Skills: {', '.join(resume.get('missing_skills', []))}
- Weak Areas: {', '.join([w.get('area', '') for w in resume.get('weak_areas', [])])}
- Questionable Claims: {', '.join([c.get('claim', '') for c in resume.get('questionable_claims', [])])}
"""
        
        job_fit_summary = f"""
JOB FIT ASSESSMENT:
- Score: {job_fit.get('score', 0)}%
- Rating: {job_fit.get('rating', 'N/A')}
- Strong Matches: {', '.join(job_fit.get('strong_matches', []))}
- Partial Matches: {', '.join(job_fit.get('partial_matches', []))}
- Missing/Weak: {', '.join(job_fit.get('missing_weak', []))}
"""

        history_summary = ""
        if history:
            history_summary = "\nINTERVIEW HISTORY:\n"
            for i, qa in enumerate(history[-5:]):
                history_summary += f"Q{i+1} ({qa.get('level', '?')}): {qa.get('question_text', '')[:100]}...\n"
                if qa.get('answer'):
                    history_summary += f"  A: {qa['answer'].get('transcript', '')[:150]}...\n"
        
        topics_str = f"\nTopics Already Covered: {', '.join(context.topics_covered)}" if context.topics_covered else ""
        weaknesses_str = f"\nIdentified Weaknesses: {', '.join(context.weaknesses_identified)}" if context.weaknesses_identified else ""
        strengths_str = f"\nConfirmed Strengths: {', '.join(context.strengths_confirmed)}" if context.strengths_confirmed else ""
        
        if is_follow_up:
            last_qa = history[-1] if history else {}
            last_question = last_qa.get('question_text', '')
            last_answer = last_qa.get('answer', {}).get('transcript', '')
            
            return f"""{jd_summary}
{resume_summary}
{job_fit_summary}
{history_summary}
{topics_str}
{weaknesses_str}
{strengths_str}

LAST QUESTION: {last_question}
CANDIDATE'S ANSWER: {last_answer}

Generate a FOLLOW-UP question that:
1. Probes deeper into the candidate's last answer
2. Challenges vague or unsubstantiated claims
3. Asks "why" or "how" for technical depth
4. Tests reasoning and decision-making
5. Adapts based on the answer quality

Return JSON:
{{
  "question_text": "...",
  "question_type": "follow_up|deep_dive|clarification|challenge",
  "expected_competencies": ["..."],
  "difficulty": "easy|medium|hard",
  "generated_context": {{"follow_up_reason": "...", "targets_weakness": true/false}}
}}"""
        
        # Initial question generation
        if level == 1:
            return f"""{jd_summary}
{resume_summary}
{job_fit_summary}

Generate {level_config['num_questions']} SCREENING interview questions for Level 1.

Focus areas: {', '.join(level_config['focus'])}
Question types: {', '.join(level_config['question_types'])}
Difficulty: {', '.join(level_config['difficulty_range'])}

Requirements:
- Reference SPECIFIC resume items (projects, roles, skills)
- Assess motivation and role understanding
- Evaluate basic communication
- Check for resume consistency
- Personalize each question to THIS candidate's background

Examples:
- "I noticed you built a RAG chatbot for your final year project. What problem did it solve and what was your specific contribution?"
- "You mentioned improving model accuracy by 18%. How did you measure that improvement?"
- "Why are you interested in this {jd.get('role_title', 'role')} position specifically?"

Return JSON array of questions:
[
  {{
    "question_text": "...",
    "question_type": "screening",
    "expected_competencies": ["..."],
    "difficulty": "easy|medium",
    "generated_context": {{"references_resume_item": "...", "personalization": "..."}}
  }}
]"""
        
        elif level == 2:
            return f"""{jd_summary}
{resume_summary}
{job_fit_summary}
{history_summary}
{topics_str}
{weaknesses_str}
{strengths_str}

Generate {level_config['num_questions']} COMPETENCY interview questions for Level 2.

Focus areas: {', '.join(level_config['focus'])}
Question types: {', '.join(level_config['question_types'])}
Difficulty: {', '.join(level_config['difficulty_range'])}

Requirements:
- Test technical competency depth
- Probe project decisions (why X over Y?)
- Assess problem-solving approach
- Evaluate behavioral competencies via STAR
- Build on Level 1 responses

Return JSON array of questions (same format as above)."""
        
        else:  # level 3
            return f"""{jd_summary}
{resume_summary}
{job_fit_summary}
{history_summary}
{topics_str}
{weaknesses_str}
{strengths_str}

Generate {level_config['num_questions']} DEEP-DIVE interview questions for Level 3.

Focus areas: {', '.join(level_config['focus'])}
Question types: {', '.join(level_config['question_types'])}
Difficulty: {', '.join(level_config['difficulty_range'])}

Requirements:
- Challenge weak or vague previous answers
- Ask "why" and "how" follow-ups
- Present realistic scenarios
- Test edge cases and trade-offs
- Identify inconsistencies
- Adapt based on ALL previous responses

Return JSON array of questions (same format as above)."""

    async def generate_initial_questions(self, context: QuestionContext) -> List[GeneratedQuestion]:
        level = context.current_level
        prompt = self._get_level_prompt(level, context)
        
        system_prompt = f"""You are an expert technical interviewer conducting a {self.LEVEL_CONFIG[level]['name']} interview. 
Generate personalized, specific questions that reference the candidate's actual resume and the job requirements.
Questions must be tailored to this specific candidate, NOT generic."""
        
        try:
            response = await llm_service.generate_text(prompt, system_prompt, temperature=0.7, max_tokens=3000)
            
            import json
            questions_data = json.loads(response)
            
            questions = []
            for q_data in questions_data:
                questions.append(GeneratedQuestion(**q_data))
            
            return questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._get_fallback_questions(level, context)

    async def generate_follow_up(self, context: QuestionContext) -> GeneratedQuestion:
        prompt = self._get_level_prompt(context.current_level, context, is_follow_up=True)
        
        system_prompt = """You are an expert interviewer generating a follow-up question. 
Analyze the candidate's last answer and create a targeted follow-up that probes deeper, challenges assumptions, or clarifies ambiguity."""
        
        try:
            response = await llm_service.generate_text(prompt, system_prompt, temperature=0.7, max_tokens=1500)
            
            import json
            q_data = json.loads(response)
            return GeneratedQuestion(**q_data)
        except Exception as e:
            print(f"Error generating follow-up: {e}")
            return GeneratedQuestion(
                question_text="Could you elaborate on that? What was your specific role and contribution?",
                question_type="follow_up",
                expected_competencies=["communication"],
                difficulty="medium",
                is_follow_up=True,
                generated_context={"fallback": True}
            )

    def _get_fallback_questions(self, level: int, context: QuestionContext) -> List[GeneratedQuestion]:
        fallbacks = {
            1: [
                GeneratedQuestion(
                    question_text=f"I see you have experience with {context.resume_analysis.get('skills', ['relevant technologies'])[0] if context.resume_analysis.get('skills') else 'relevant technologies'}. Can you walk me through a project where you used this?",
                    question_type="screening",
                    expected_competencies=["technical_knowledge", "communication"],
                    difficulty="easy",
                    generated_context={"fallback": True}
                ),
                GeneratedQuestion(
                    question_text=f"What interests you most about the {context.jd_analysis.get('role_title', 'this role')} position?",
                    question_type="screening",
                    expected_competencies=["motivation", "role_fit"],
                    difficulty="easy",
                    generated_context={"fallback": True}
                ),
            ],
            2: [
                GeneratedQuestion(
                    question_text="Describe a challenging technical problem you solved recently. What was your approach?",
                    question_type="technical",
                    expected_competencies=["problem_solving", "technical_knowledge"],
                    difficulty="medium",
                    generated_context={"fallback": True}
                ),
                GeneratedQuestion(
                    question_text="Tell me about a time you had to make a difficult technical decision with incomplete information.",
                    question_type="behavioral",
                    expected_competencies=["decision_making", "problem_solving"],
                    difficulty="medium",
                    generated_context={"fallback": True}
                ),
            ],
            3: [
                GeneratedQuestion(
                    question_text="How would you design a system to handle the scale requirements mentioned in this role?",
                    question_type="deep_dive",
                    expected_competencies=["system_design", "technical_depth"],
                    difficulty="hard",
                    generated_context={"fallback": True}
                ),
                GeneratedQuestion(
                    question_text="What are the trade-offs between the approaches you mentioned? When would you choose one over the other?",
                    question_type="deep_dive",
                    expected_competencies=["technical_depth", "reasoning"],
                    difficulty="hard",
                    generated_context={"fallback": True}
                ),
            ]
        }
        return fallbacks.get(level, fallbacks[1])

    def calculate_difficulty_adjustment(self, interview_state: Dict[str, Any], last_answer_quality: float) -> float:
        current_adjustment = interview_state.get("difficulty_adjustment", 0.0)
        
        if last_answer_quality >= 0.8:
            return min(current_adjustment + 0.15, 1.0)
        elif last_answer_quality >= 0.6:
            return current_adjustment
        elif last_answer_quality >= 0.4:
            return max(current_adjustment - 0.1, -1.0)
        else:
            return max(current_adjustment - 0.2, -1.0)

    def should_generate_follow_up(self, answer: Dict[str, Any], question: Dict[str, Any]) -> bool:
        transcript = answer.get("transcript", "").lower()
        
        if len(transcript.split()) < 20:
            return True
        
        vague_indicators = ["i don't know", "not sure", "maybe", "i think", "sort of", "kind of", "basically", "just"]
        vague_count = sum(1 for ind in vague_indicators if ind in transcript)
        if vague_count >= 2:
            return True
        
        claim_indicators = ["improved", "increased", "reduced", "optimized", "built", "designed", "implemented", "achieved"]
        has_claims = any(ind in transcript for ind in claim_indicators)
        has_numbers = any(c.isdigit() for c in transcript)
        if has_claims and not has_numbers:
            return True
        
        return False


interview_service = InterviewService()