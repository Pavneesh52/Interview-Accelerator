"use client"

import { useEffect, useState, useRef } from "react"
import { InterviewQuestion } from "@/lib/types"

interface AIInterviewerProps {
  question: InterviewQuestion | null
  isSpeaking: boolean
  isThinking: boolean
  interviewerName: string
}

export function AIInterviewer({ question, isSpeaking, isThinking, interviewerName }: AIInterviewerProps) {
  const [displayedText, setDisplayedText] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const prevQuestionRef = useRef<string>("")

  // Typing animation effect for new questions
  useEffect(() => {
    if (!question?.question_text || question.question_text === prevQuestionRef.current) return

    prevQuestionRef.current = question.question_text
    const fullText = question.question_text
    setIsTyping(true)
    setDisplayedText("")

    let i = 0
    const speed = 20 // ms per character
    const timer = setInterval(() => {
      if (i < fullText.length) {
        setDisplayedText(fullText.slice(0, i + 1))
        i++
      } else {
        clearInterval(timer)
        setIsTyping(false)
      }
    }, speed)

    return () => clearInterval(timer)
  }, [question?.question_text])

  const getLevelGradient = () => {
    return "bg-white text-black font-bold border border-white/30"
  }

  const getQuestionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      screening: "Screening",
      technical: "Technical",
      behavioral: "Behavioral",
      scenario: "Scenario",
      follow_up: "Follow-up",
      deep_dive: "Deep Dive",
    }
    return labels[type] || type
  }

  const getDifficultyColor = (diff: string) => {
    return "text-white bg-white/10 border-white/20 font-medium"
  }

  return (
    <div className="flex flex-col h-full">
      {/* Interviewer Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative">
          <div
            className={`w-12 h-12 rounded-full bg-white text-black font-extrabold text-lg flex items-center justify-center shadow-lg ${
              isSpeaking ? "animate-avatar-speak" : ""
            }`}
          >
            {interviewerName.charAt(0)}
          </div>
          {/* Status Indicator */}
          <div
            className={`absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-black ${
              isThinking
                ? "bg-neutral-400 animate-pulse"
                : isSpeaking
                ? "bg-white"
                : "bg-neutral-600"
            }`}
          />
        </div>
        <div>
          <h3 className="text-white font-semibold text-sm">{interviewerName}</h3>
          <p className="text-white/40 text-xs">
            {isThinking ? "Thinking..." : isSpeaking ? "Speaking..." : "Listening"}
          </p>
        </div>

        {/* Audio waveform when speaking */}
        {isSpeaking && (
          <div className="flex items-center gap-[3px] ml-auto">
            {[1, 2, 3, 2, 1, 3, 2].map((v, i) => (
              <div
                key={i}
                className={`w-[3px] bg-white rounded-full ${
                  v === 1 ? "animate-waveform-1" : v === 2 ? "animate-waveform-2" : "animate-waveform-3"
                }`}
                style={{ height: `${8 + v * 4}px` }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Question Area */}
      <div className="flex-1 flex flex-col">
        {isThinking && !question ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="flex justify-center gap-1.5">
                <div className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <p className="text-white/40 text-sm">Preparing your next question...</p>
            </div>
          </div>
        ) : question ? (
          <div className="space-y-4 animate-fade-in">
            {/* Question Metadata */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wide border ${getDifficultyColor(question.difficulty)}`}>
                {question.difficulty}
              </span>
              <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-medium bg-white/5 border border-white/10 text-white/60">
                {getQuestionTypeLabel(question.question_type)}
              </span>
              {question.is_follow_up && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-medium bg-violet-400/10 border border-violet-400/20 text-violet-400">
                  ↩ Follow-up
                </span>
              )}
            </div>

            {/* Question Text */}
            <div className="p-5 rounded-2xl bg-white/[0.04] border border-white/[0.06]">
              <p className="text-white text-lg leading-relaxed font-medium">
                {displayedText}
                {isTyping && <span className="animate-blink text-indigo-400 ml-0.5">|</span>}
              </p>
            </div>

            {/* Context - what's being evaluated */}
            {question.expected_competencies.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[11px] text-white/30 uppercase tracking-wider font-medium">Evaluating:</span>
                {question.expected_competencies.map((comp) => (
                  <span
                    key={comp}
                    className="text-[11px] text-white/40 bg-white/[0.03] px-2 py-0.5 rounded"
                  >
                    {comp.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}

            {/* Follow-up context */}
            {question.is_follow_up && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-violet-400/5 border border-violet-400/10">
                <span className="text-violet-400 text-sm mt-0.5">💡</span>
                <p className="text-xs text-violet-300/70">
                  This follow-up was generated based on your previous answer to explore the topic deeper.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-white/30 text-sm">Waiting for question...</p>
          </div>
        )}
      </div>
    </div>
  )
}
