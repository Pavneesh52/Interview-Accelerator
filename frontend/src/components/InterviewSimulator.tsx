"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { SkipForward, Pause, Play, Volume2, VolumeX, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { toast } from "@/components/ui/use-toast"
import { Interview, InterviewerIntro, InterviewPhase, InterviewQuestion } from "@/lib/types"
import { InterviewLobby } from "@/components/InterviewLobby"
import { AIInterviewer } from "@/components/AIInterviewer"
import { CandidateResponse } from "@/components/CandidateResponse"
import { InterviewProgress } from "@/components/InterviewProgress"
import { InterviewComplete } from "@/components/InterviewComplete"

interface InterviewSimulatorProps {
  sessionId: string
  onExit: () => void
}

export function InterviewSimulator({ sessionId, onExit }: InterviewSimulatorProps) {
  const [phase, setPhase] = useState<InterviewPhase>("lobby")
  const [interview, setInterview] = useState<Interview | null>(null)
  const [intro, setIntro] = useState<InterviewerIntro | null>(null)
  const [loading, setLoading] = useState(true)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const [isPaused, setIsPaused] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  // Load or create interview on mount
  useEffect(() => {
    loadInterview()
  }, [sessionId])

  const loadInterview = async () => {
    setLoading(true)
    try {
      // Try to get existing interview for this session
      try {
        const res = await api.get(`/interviews/interviews/session/${sessionId}`)
        const interviewData = res.data as Interview
        setInterview(interviewData)

        if (interviewData.status === "completed") {
          setPhase("complete")
        } else if (interviewData.status === "in_progress") {
          // Load intro and go to active if there are already answered questions
          await loadIntro(interviewData.id)
          const hasAnswers = interviewData.questions.some((q) => q.answer)
          setPhase(hasAnswers ? "active" : "lobby")
        }
        return
      } catch {
        // No existing interview — will create on begin
      }

      // No interview yet — stay in lobby but pre-generate intro after creating
      setPhase("lobby")
    } catch (error) {
      toast({ title: "Error", description: "Failed to load interview data", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const loadIntro = async (interviewId: string) => {
    try {
      const res = await api.get(`/interviews/interviews/${interviewId}/intro`)
      setIntro(res.data)
    } catch {
      // Intro is optional, use fallback
      setIntro({
        greeting: "Hi there! I'll be your interviewer today. Let's have a conversation about your background and how it connects to this role. Ready to begin?",
        interviewer_name: "Alex",
        interviewer_title: "Senior Technical Interviewer",
        focus_areas: ["Your background", "Motivation", "Role understanding", "Communication"],
        estimated_duration_minutes: 15,
        tips: [
          "Speak naturally — this is a conversation",
          "Use specific examples from your experience",
          "It's okay to pause and think",
        ],
      })
    }
  }

  const handleBeginInterview = async () => {
    setLoading(true)
    try {
      let interviewData = interview

      if (!interviewData) {
        // Start a new interview
        const res = await api.post("/interviews/interviews/start", {
          session_id: sessionId,
        })
        interviewData = res.data as Interview
        setInterview(interviewData)
        await loadIntro(interviewData.id)
      }

      setPhase("active")

      // Speak the first question if TTS is enabled
      if (ttsEnabled && interviewData.questions?.[0]) {
        setTimeout(() => {
          speakText(interviewData!.questions[0].question_text)
        }, 500)
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to start interview"
      toast({ title: "Error", description: message, variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const speakText = useCallback(
    (text: string) => {
      if (!ttsEnabled || !("speechSynthesis" in window)) return

      // Cancel any ongoing speech
      speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.95
      utterance.pitch = 1
      utterance.volume = 0.9

      // Try to pick a natural voice
      const voices = speechSynthesis.getVoices()
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Neural"))
      )
      if (preferred) utterance.voice = preferred

      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      utterance.onerror = () => setIsSpeaking(false)

      utteranceRef.current = utterance
      speechSynthesis.speak(utterance)
    },
    [ttsEnabled]
  )

  const handleSubmitAnswer = async (transcript: string, durationSeconds: number) => {
    if (!interview) return

    const currentQ = interview.questions[interview.current_question_index]
    if (!currentQ) return

    setIsThinking(true)

    try {
      // Submit the answer
      await api.post(`/interviews/interviews/questions/${currentQ.id}/answer`, {
        transcript,
        duration_seconds: durationSeconds,
      })

      // Refresh interview state
      const res = await api.get(`/interviews/interviews/${interview.id}`)
      const updated = res.data as Interview
      setInterview(updated)

      // Check if interview is completed
      if (updated.current_question_index >= updated.total_questions) {
        // Mark complete
        await api.post(`/interviews/interviews/${interview.id}/complete`)
        const finalRes = await api.get(`/interviews/interviews/${interview.id}`)
        setInterview(finalRes.data as Interview)
        setIsThinking(false)
        setPhase("complete")

        // Trigger evaluation in background
        try {
          await api.post(`/interviews/interviews/${interview.id}/evaluate`)
        } catch {
          // Evaluation errors are non-blocking
        }
        return
      }

      // Get next question (may generate follow-up)
      try {
        const nextRes = await api.post(`/interviews/interviews/${interview.id}/next-question`)
        // Refresh interview state to include the follow-up if generated
        const refreshed = await api.get(`/interviews/interviews/${interview.id}`)
        setInterview(refreshed.data as Interview)

        // Speak the next question
        if (ttsEnabled && nextRes.data?.question_text) {
          setTimeout(() => speakText(nextRes.data.question_text), 300)
        }
      } catch {
        // If next-question fails (e.g., interview completed), refresh
        const refreshed = await api.get(`/interviews/interviews/${interview.id}`)
        const refreshedData = refreshed.data as Interview
        setInterview(refreshedData)

        if (refreshedData.status === "completed") {
          setPhase("complete")
        }
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to submit answer"
      toast({ title: "Error", description: message, variant: "destructive" })
    } finally {
      setIsThinking(false)
    }
  }

  const handleSkipQuestion = async () => {
    if (!interview) return

    setIsThinking(true)
    try {
      const res = await api.post(`/interviews/interviews/${interview.id}/skip-question`)

      // Refresh interview state
      const refreshed = await api.get(`/interviews/interviews/${interview.id}`)
      const updated = refreshed.data as Interview
      setInterview(updated)

      // Check if interview is completed
      if (updated.current_question_index >= updated.total_questions) {
        await api.post(`/interviews/interviews/${interview.id}/complete`)
        const finalRes = await api.get(`/interviews/interviews/${interview.id}`)
        setInterview(finalRes.data as Interview)
        setPhase("complete")
        return
      }

      // Speak next question
      if (ttsEnabled && res.data?.question_text) {
        setTimeout(() => speakText(res.data.question_text), 300)
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to skip question"
      toast({ title: "Error", description: message, variant: "destructive" })
    } finally {
      setIsThinking(false)
    }
  }

  const handleToggleTTS = () => {
    if (isSpeaking) {
      speechSynthesis.cancel()
      setIsSpeaking(false)
    }
    setTtsEnabled(!ttsEnabled)
  }

  const handlePause = () => {
    if (isSpeaking) {
      speechSynthesis.cancel()
      setIsSpeaking(false)
    }
    setIsPaused(!isPaused)
  }

  const handleEndInterview = async () => {
    if (!interview) return

    if (isSpeaking) {
      speechSynthesis.cancel()
      setIsSpeaking(false)
    }

    try {
      await api.post(`/interviews/interviews/${interview.id}/complete`)
      const res = await api.get(`/interviews/interviews/${interview.id}`)
      setInterview(res.data as Interview)
      setPhase("complete")

      // Trigger evaluation
      try {
        await api.post(`/interviews/interviews/${interview.id}/evaluate`)
      } catch {
        // Non-blocking
      }
    } catch (error: any) {
      toast({ title: "Error", description: "Failed to end interview", variant: "destructive" })
    }
  }

  const currentQuestion: InterviewQuestion | null =
    interview?.questions?.[interview.current_question_index] || null

  // ========== RENDER ==========

  if (phase === "lobby") {
    return (
      <InterviewLobby
        intro={intro}
        level={interview?.current_level || 1}
        loading={loading}
        onBegin={handleBeginInterview}
      />
    )
  }

  if (phase === "complete" && interview) {
    return (
      <InterviewComplete
        interview={interview}
        sessionId={sessionId}
        onViewResults={() => {}}
      />
    )
  }

  if (!interview) {
    return (
      <div className="min-h-screen interview-bg-gradient flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  // ========== ACTIVE INTERVIEW ==========
  return (
    <div className="min-h-screen interview-bg-gradient flex flex-col">
      {/* Top Bar */}
      <header className="shrink-0 border-b border-white/[0.06] bg-white/[0.02] backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Left: Progress */}
          <InterviewProgress interview={interview} />

          {/* Right: Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggleTTS}
              className="text-white/40 hover:text-white/70 hover:bg-white/5 h-9 w-9 p-0 cursor-pointer"
              title={ttsEnabled ? "Mute interviewer voice" : "Unmute interviewer voice"}
            >
              {ttsEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkipQuestion}
              disabled={isThinking || isPaused}
              className="text-white/40 hover:text-white/70 hover:bg-white/5 h-9 px-3 text-xs cursor-pointer"
              title="Skip this question"
            >
              <SkipForward className="h-3.5 w-3.5 mr-1.5" />
              Skip
            </Button>

            <div className="w-px h-6 bg-white/10 mx-1" />

            <Button
              variant="ghost"
              size="sm"
              onClick={handleEndInterview}
              className="text-red-400/60 hover:text-red-400 hover:bg-red-400/5 h-9 px-3 text-xs cursor-pointer"
              title="End interview early"
            >
              <LogOut className="h-3.5 w-3.5 mr-1.5" />
              End
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content: Split View */}
      <main className="flex-1 flex flex-col lg:flex-row max-w-7xl mx-auto w-full">
        {/* Left Panel: AI Interviewer */}
        <div className="lg:w-1/2 p-4 sm:p-6 lg:p-8 lg:border-r border-white/[0.04] flex flex-col">
          <AIInterviewer
            question={currentQuestion}
            isSpeaking={isSpeaking}
            isThinking={isThinking}
            interviewerName={intro?.interviewer_name || "Alex"}
          />
        </div>

        {/* Right Panel: Candidate Response */}
        <div className="lg:w-1/2 p-4 sm:p-6 lg:p-8 flex flex-col border-t lg:border-t-0 border-white/[0.04]">
          <CandidateResponse
            onSubmit={handleSubmitAnswer}
            disabled={isThinking || isPaused || !currentQuestion}
            questionId={currentQuestion?.id || null}
          />
        </div>
      </main>

      {/* Paused Overlay */}
      {isPaused && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center animate-fade-in">
          <div className="text-center space-y-6 animate-scale-in">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white/5 border border-white/10">
              <Pause className="h-10 w-10 text-white/60" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Interview Paused</h2>
              <p className="text-white/40 mt-1 text-sm">Take a moment to collect your thoughts</p>
            </div>
            <Button
              onClick={handlePause}
              size="lg"
              className="bg-white text-black hover:bg-neutral-200 font-medium px-8 rounded-xl shadow-xl cursor-pointer"
            >
              <Play className="h-5 w-5 mr-2" />
              Resume Interview
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
