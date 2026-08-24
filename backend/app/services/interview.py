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


class InterviewerIntro(BaseModel):
    greeting: str
    interviewer_name: str
    interviewer_title: str
    focus_areas: List[str]
    estimated_duration_minutes: int
    tips: List[str]


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
            "estimated_duration": 15,
        },
        2: {
            "name": "Competency",
            "num_questions": 7,
            "focus": ["technical_knowledge", "problem_solving", "projects", "behavioral_competencies", "decision_making"],
            "question_types": ["technical", "behavioral", "scenario"],
            "difficulty_range": ["medium", "hard"],
            "estimated_duration": 25,
        },
        3: {
            "name": "Deep-Dive",
            "num_questions": 10,
            "focus": ["technical_depth", "reasoning", "edge_cases", "trade_offs", "challenges", "inconsistencies"],
            "question_types": ["deep_dive", "scenario", "follow_up"],
            "difficulty_range": ["hard"],
            "estimated_duration": 35,
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

    async def generate_interviewer_intro(self, context: QuestionContext) -> InterviewerIntro:
        """Generate a personalized interviewer introduction for the candidate."""
        level = context.current_level
        level_config = self.LEVEL_CONFIG[level]
        jd = context.jd_analysis
        resume = context.resume_analysis

        candidate_skills = resume.get("skills", [])[:5]
        role_title = jd.get("role_title", "this role")
        projects = resume.get("projects", [])

        project_mention = ""
        if projects:
            first_project = projects[0] if isinstance(projects[0], dict) else {}
            project_name = first_project.get("name", "")
            if project_name:
                project_mention = f" I noticed some interesting projects on your profile, like {project_name}, and I'm looking forward to hearing more about them."

        skills_mention = ""
        if candidate_skills:
            skills_mention = f" Your background in {', '.join(candidate_skills[:3])} caught my attention."

        greeting = (
            f"Hi there! I'm Alex, and I'll be your interviewer today for the {role_title} position. "
            f"This is a {level_config['name'].lower()} round where we'll have a conversation about your background "
            f"and what motivates you.{skills_mention}{project_mention} "
            f"There are no trick questions — I just want to understand your experience and how it connects to this role. "
            f"Feel free to take your time with each answer. Ready to begin?"
        )

        focus_labels = {
            "resume": "Your background & experience",
            "motivation": "What drives you",
            "basic_understanding": "Role understanding",
            "role_fit": "How your skills align",
            "communication": "How you articulate ideas",
            "relevant_experience": "Relevant past work",
            "career_goals": "Where you're headed",
        }

        return InterviewerIntro(
            greeting=greeting,
            interviewer_name="Alex",
            interviewer_title="Senior Technical Interviewer",
            focus_areas=[focus_labels.get(f, f.replace("_", " ").title()) for f in level_config["focus"]],
            estimated_duration_minutes=level_config["estimated_duration"],
            tips=[
                "Speak naturally — this is a conversation, not a test",
                "Use specific examples from your experience",
                "It's okay to pause and think before answering",
                "If you're unsure about something, say so honestly",
                "Reference specific projects, numbers, or outcomes when possible",
            ],
        )

    def _build_jd_summary(self, jd: Dict[str, Any]) -> str:
        return f"""
JOB DESCRIPTION ANALYSIS:
- Role: {jd.get('role_title', 'N/A')}
- Required Skills: {', '.join(jd.get('required_skills', []))}
- Preferred Skills: {', '.join(jd.get('preferred_skills', []))}
- Technical Competencies: {', '.join([c.get('name', '') for c in jd.get('technical_competencies', [])])}
- Behavioral Competencies: {', '.join([c.get('name', '') for c in jd.get('behavioral_competencies', [])])}
- Experience Expectations: {jd.get('experience_expectations', 'N/A')}
- Keywords: {', '.join(jd.get('keywords', []))}
"""

    def _build_resume_summary(self, resume: Dict[str, Any]) -> str:
        # Build detailed experience lines
        experience_details = []
        for exp in resume.get("experience", []):
            if isinstance(exp, dict):
                role = exp.get("role", "")
                company = exp.get("company", "")
                desc = exp.get("description", "")[:100]
                experience_details.append(f"  - {role} at {company}: {desc}")

        # Build detailed project lines
        project_details = []
        for proj in resume.get("projects", []):
            if isinstance(proj, dict):
                name = proj.get("name", "")
                desc = proj.get("description", "")[:100]
                techs = ", ".join(proj.get("technologies", [])[:5])
                impact = proj.get("impact", "")[:80]
                project_details.append(f"  - {name} ({techs}): {desc} | Impact: {impact}")

        return f"""
CANDIDATE RESUME ANALYSIS:
- Skills: {', '.join(resume.get('skills', []))}
- Experience ({len(resume.get('experience', []))} roles):
{chr(10).join(experience_details) if experience_details else '  (none listed)'}
- Projects ({len(resume.get('projects', []))} projects):
{chr(10).join(project_details) if project_details else '  (none listed)'}
- Achievements: {', '.join(resume.get('achievements', [])[:5])}
- Strengths: {', '.join(resume.get('strengths', []))}
- Missing Skills (vs JD): {', '.join(resume.get('missing_skills', []))}
- Weak Areas: {', '.join([w.get('area', '') for w in resume.get('weak_areas', [])])}
- Questionable Claims: {', '.join([c.get('claim', '') for c in resume.get('questionable_claims', [])])}
"""

    def _build_job_fit_summary(self, job_fit: Dict[str, Any]) -> str:
        return f"""
JOB FIT ASSESSMENT:
- Score: {job_fit.get('score', 0)}%
- Rating: {job_fit.get('rating', 'N/A')}
- Strong Matches: {', '.join(job_fit.get('strong_matches', []))}
- Partial Matches: {', '.join(job_fit.get('partial_matches', []))}
- Missing/Weak: {', '.join(job_fit.get('missing_weak', []))}
"""

    def _build_history_summary(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return ""
        summary = "\nINTERVIEW HISTORY:\n"
        for i, qa in enumerate(history[-5:]):
            summary += f"Q{i+1} ({qa.get('level', '?')}): {qa.get('question_text', '')[:100]}...\n"
            if qa.get('answer'):
                summary += f"  A: {qa['answer'].get('transcript', '')[:150]}...\n"
        return summary

    def _get_level_prompt(self, level: int, context: QuestionContext, is_follow_up: bool = False) -> str:
        level_config = self.LEVEL_CONFIG[level]

        jd = context.jd_analysis
        resume = context.resume_analysis
        job_fit = context.job_fit
        history = context.interview_history

        jd_summary = self._build_jd_summary(jd)
        resume_summary = self._build_resume_summary(resume)
        job_fit_summary = self._build_job_fit_summary(job_fit)
        history_summary = self._build_history_summary(history)

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
  "question_type": "follow_up",
  "expected_competencies": ["..."],
  "difficulty": "easy|medium|hard",
  "generated_context": {{
    "follow_up_reason": "...",
    "targets_weakness": true/false,
    "resume_reference": "what specific resume item this relates to",
    "evaluation_focus": "what the interviewer is looking for in this follow-up"
  }}
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

CRITICAL Requirements for personalization:
- Each question MUST reference a SPECIFIC item from the candidate's resume (a named project, a specific role, a particular skill, a concrete achievement, or a claim)
- DO NOT ask generic questions like "Tell me about yourself" or "What are your strengths"
- Assess motivation and understanding of THIS specific role
- Probe questionable or unsubstantiated claims from the resume
- Questions should feel like a natural conversation, not a quiz

Examples of GOOD personalized questions:
- "I noticed you built a RAG chatbot for your final year project. What problem did it solve and what was your specific contribution?"
- "You mentioned improving model accuracy by 18%. How did you measure that improvement?"
- "Your experience at [Company] involved [specific responsibility]. How would that translate to the {jd.get('role_title', 'role')} we're hiring for?"
- "I see you've worked with [skill]. The role requires [related JD requirement]. How comfortable are you bridging that gap?"

Examples of BAD generic questions (DO NOT generate these):
- "Tell me about yourself"
- "What are your strengths and weaknesses?"
- "Why should we hire you?"
- "Where do you see yourself in 5 years?"

Return a JSON array of questions:
[
  {{
    "question_text": "...",
    "question_type": "screening",
    "expected_competencies": ["..."],
    "difficulty": "easy|medium",
    "generated_context": {{
      "resume_reference": "the specific resume item this question targets (e.g., 'RAG chatbot project', 'role at XYZ Corp')",
      "evaluation_focus": "what the interviewer is specifically looking for in the answer",
      "ideal_answer_hints": "brief notes on what a strong answer would include",
      "personalization": "how this question is personalized to this candidate"
    }}
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
- Reference specific items from the resume and previous answers

Return JSON array of questions with the same schema as above, including generated_context with resume_reference, evaluation_focus, ideal_answer_hints."""

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

Return JSON array of questions with the same schema as above, including generated_context with resume_reference, evaluation_focus, ideal_answer_hints."""

    async def generate_initial_questions(self, context: QuestionContext) -> List[GeneratedQuestion]:
        level = context.current_level
        prompt = self._get_level_prompt(level, context)

        system_prompt = f"""You are an expert technical interviewer conducting a {self.LEVEL_CONFIG[level]['name']} interview.
You are warm, professional, and conversational — like a senior engineer having a genuine conversation, NOT a robotic quiz master.

Your questions must be:
1. Personalized to THIS specific candidate's resume and background
2. Natural and conversational in tone
3. Specific — referencing named projects, roles, skills, or achievements from the resume
4. Designed to evaluate the candidate fairly while making them feel comfortable

Generate personalized, specific questions that reference the candidate's actual resume and the job requirements.
Return ONLY valid JSON array, no markdown formatting or code fences."""

        try:
            response = await llm_service.generate_text(prompt, system_prompt, temperature=0.7, max_tokens=4000)

            import json
            # Strip any markdown code fences the LLM might add
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            questions_data = json.loads(cleaned)

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
Analyze the candidate's last answer and create a targeted follow-up that probes deeper, challenges assumptions, or clarifies ambiguity.
Be conversational and natural. Return ONLY valid JSON, no markdown formatting or code fences."""

        try:
            response = await llm_service.generate_text(prompt, system_prompt, temperature=0.7, max_tokens=1500)

            import json
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            q_data = json.loads(cleaned)
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
        # Extract specific resume items for more personalized fallbacks
        skills = context.resume_analysis.get('skills', [])
        first_skill = skills[0] if skills else 'relevant technologies'
        role_title = context.jd_analysis.get('role_title', 'this role')
        projects = context.resume_analysis.get('projects', [])
        experience = context.resume_analysis.get('experience', [])
        achievements = context.resume_analysis.get('achievements', [])
        questionable_claims = context.resume_analysis.get('questionable_claims', [])

        first_project_name = ""
        if projects:
            p = projects[0] if isinstance(projects[0], dict) else {}
            first_project_name = p.get("name", "your most recent project")

        first_exp_role = ""
        first_exp_company = ""
        if experience:
            e = experience[0] if isinstance(experience[0], dict) else {}
            first_exp_role = e.get("role", "your previous role")
            first_exp_company = e.get("company", "your previous company")

        fallbacks = {
            1: [
                GeneratedQuestion(
                    question_text=f"I see you have experience with {first_skill}. Can you walk me through a project where you used this and what challenges you faced?",
                    question_type="screening",
                    expected_competencies=["technical_knowledge", "communication"],
                    difficulty="easy",
                    generated_context={"fallback": True, "resume_reference": first_skill}
                ),
                GeneratedQuestion(
                    question_text=f"What interests you most about the {role_title} position, and how does it connect to where you want your career to go?",
                    question_type="screening",
                    expected_competencies=["motivation", "role_fit"],
                    difficulty="easy",
                    generated_context={"fallback": True, "resume_reference": role_title}
                ),
                GeneratedQuestion(
                    question_text=f"Tell me about {first_project_name}. What was the problem you were solving, and what was your specific contribution?",
                    question_type="screening",
                    expected_competencies=["communication", "technical_knowledge"],
                    difficulty="easy",
                    generated_context={"fallback": True, "resume_reference": first_project_name}
                ),
                GeneratedQuestion(
                    question_text=f"During your time as {first_exp_role} at {first_exp_company}, what was the most impactful thing you accomplished?",
                    question_type="screening",
                    expected_competencies=["communication", "role_fit"],
                    difficulty="medium",
                    generated_context={"fallback": True, "resume_reference": f"{first_exp_role} at {first_exp_company}"}
                ),
                GeneratedQuestion(
                    question_text=f"Looking at the requirements for {role_title}, which areas do you feel most confident in, and where would you need to ramp up?",
                    question_type="screening",
                    expected_competencies=["self_awareness", "role_fit"],
                    difficulty="medium",
                    generated_context={"fallback": True, "resume_reference": "overall fit"}
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

    def compute_speech_analytics(self, transcript: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Compute basic speech analytics from transcript text."""
        if not transcript:
            return {"filler_words_count": 0, "word_count": 0, "speaking_pace_wpm": None, "long_pauses_count": 0}

        words = transcript.split()
        word_count = len(words)

        filler_words = ["um", "uh", "like", "you know", "basically", "actually", "literally", "sort of", "kind of", "i mean", "right", "so yeah"]
        transcript_lower = transcript.lower()
        filler_count = sum(transcript_lower.count(fw) for fw in filler_words)

        speaking_pace = None
        if duration_seconds and duration_seconds > 0:
            speaking_pace = round((word_count / duration_seconds) * 60, 1)

        # Estimate long pauses from repeated spaces or ellipsis patterns
        long_pauses = transcript.count("...") + transcript.count("…")

        return {
            "filler_words_count": filler_count,
            "word_count": word_count,
            "speaking_pace_wpm": speaking_pace,
            "long_pauses_count": long_pauses,
        }


interview_service = InterviewService()