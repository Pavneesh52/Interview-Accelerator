export interface User {
  id: string
  email: string
  full_name: string | null
  avatar_url: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface JobDescription {
  id: string
  user_id: string
  title: string
  raw_text: string
  file_url: string | null
  file_name: string | null
  file_size: number | null
  parsed_json: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Resume {
  id: string
  user_id: string
  raw_text: string
  file_url: string | null
  file_name: string | null
  file_size: number | null
  parsed_json: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface TechnicalCompetency {
  name: string
  description: string
  importance: "high" | "medium" | "low"
}

export interface BehavioralCompetency {
  name: string
  description: string
  importance: "high" | "medium" | "low"
}

export interface JDAnalysis {
  id: string
  session_id: string
  role_title: string
  responsibilities: string[]
  required_skills: string[]
  preferred_skills: string[]
  technical_competencies: TechnicalCompetency[]
  behavioral_competencies: BehavioralCompetency[]
  experience_expectations: string | null
  keywords: string[]
  concepts: string[]
  qualifications: string[]
  created_at: string
}

export interface ExperienceItem {
  role: string
  company: string
  duration: string
  description: string
}

export interface ProjectItem {
  name: string
  description: string
  technologies: string[]
  impact: string
}

export interface WeakArea {
  area: string
  reason: string
}

export interface QuestionableClaim {
  claim: string
  why_questionable: string
  follow_up_questions: string[]
}

export interface ResumeAnalysis {
  id: string
  session_id: string
  skills: string[]
  experience: ExperienceItem[]
  projects: ProjectItem[]
  achievements: string[]
  strengths: string[]
  missing_skills: string[]
  weak_areas: WeakArea[]
  questionable_claims: QuestionableClaim[]
  created_at: string
}

export interface JobFitAssessment {
  id: string
  session_id: string
  score: number
  rating: string
  strong_matches: string[]
  partial_matches: string[]
  missing_weak: string[]
  methodology: string | null
  skill_match_details: Record<string, unknown> | null
  created_at: string
}

export type SessionStatus = "pending" | "processing" | "completed" | "failed"

export interface AnalysisSession {
  id: string
  user_id: string
  jd_id: string
  resume_id: string
  status: SessionStatus
  created_at: string
  updated_at: string
  completed_at: string | null
  jd_analysis: JDAnalysis | null
  resume_analysis: ResumeAnalysis | null
  job_fit: JobFitAssessment | null
}

export interface SessionCreate {
  jd_id: string
  resume_id: string
}

export type InterviewStatus = "not_started" | "in_progress" | "paused" | "completed" | "abandoned"
export type InterviewLevel = 1 | 2 | 3
export type QuestionType = "screening" | "technical" | "behavioral" | "scenario" | "follow_up" | "deep_dive"
export type DifficultyLevel = "easy" | "medium" | "hard"
export type ReadinessLevel = "not_ready" | "needs_preparation" | "interview_ready" | "strong_candidate"

export interface InterviewQuestion {
  id: string
  interview_id: string
  level: InterviewLevel
  question_text: string
  question_type: QuestionType
  expected_competencies: string[]
  difficulty: DifficultyLevel
  order_index: number
  is_follow_up: boolean
  parent_question_id: string | null
  asked_at: string | null
  answer?: InterviewAnswer
}

export interface InterviewAnswer {
  id: string
  question_id: string
  transcript: string | null
  audio_url: string | null
  video_url: string | null
  duration_seconds: number | null
  confidence_score: number | null
  filler_words_count: number
  speaking_pace_wpm: number | null
  long_pauses_count: number
  submitted_at: string
}

export interface QuestionFeedback {
  question_id: string
  question: string
  candidate_answer: string
  assessment: string
  what_was_good: string[]
  what_could_be_better: string[]
  ideal_direction: string
  competencies_evaluated: string[]
  score: number
}

export interface PreparationGap {
  priority: number
  topic: string
  review_items: string[]
}

export interface InterviewEvaluation {
  id: string
  interview_id: string
  overall_score: number | null
  role_fit_score: number | null
  technical_knowledge_score: number | null
  problem_solving_score: number | null
  communication_score: number | null
  confidence_score: number | null
  depth_of_understanding_score: number | null
  behavioral_fit_score: number | null
  competency_scores: Record<string, number> | null
  question_feedbacks: QuestionFeedback[]
  strengths: string[]
  weaknesses: string[]
  preparation_gaps: PreparationGap[]
  readiness_level: ReadinessLevel | null
  readiness_score: number | null
  created_at: string
}

export interface Interview {
  id: string
  session_id: string
  status: InterviewStatus
  current_level: InterviewLevel
  current_question_index: number
  total_questions: number
  started_at: string | null
  completed_at: string | null
  difficulty_adjustment: number
  topics_covered: string[]
  weaknesses_identified: string[]
  strengths_confirmed: string[]
  questions: InterviewQuestion[]
  evaluation: InterviewEvaluation | null
}

export interface StartInterviewRequest {
  session_id: string
}