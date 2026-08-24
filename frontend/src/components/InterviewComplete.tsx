"use client"

import { useEffect, useState } from "react"
import { Trophy, Clock, BarChart3, ArrowRight, ChevronRight, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Interview } from "@/lib/types"
import Link from "next/link"

interface InterviewCompleteProps {
  interview: Interview
  sessionId: string
  onViewResults: () => void
}

export function InterviewComplete({ interview, sessionId, onViewResults }: InterviewCompleteProps) {
  const [showStats, setShowStats] = useState(false)
  const [showCTA, setShowCTA] = useState(false)
  const [confetti, setConfetti] = useState<Array<{ x: number; delay: number; color: string }>>([])

  useEffect(() => {
    // Generate confetti pieces
    const pieces = Array.from({ length: 30 }, (_, i) => ({
      x: Math.random() * 100,
      delay: Math.random() * 2,
      color: ["#6366f1", "#8b5cf6", "#a78bfa", "#60a5fa", "#34d399", "#fbbf24", "#f472b6"][i % 7],
    }))
    setConfetti(pieces)

    const t1 = setTimeout(() => setShowStats(true), 600)
    const t2 = setTimeout(() => setShowCTA(true), 1200)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [])

  const answeredQuestions = interview.questions.filter(
    (q) => q.answer && q.answer.transcript !== "[SKIPPED]"
  )
  const skippedQuestions = interview.questions.filter(
    (q) => q.answer?.transcript === "[SKIPPED]"
  )

  // Calculate total duration from answered questions
  const totalDuration = answeredQuestions.reduce(
    (sum, q) => sum + (q.answer?.duration_seconds || 0), 0
  )

  const levelNames: Record<number, string> = { 1: "Screening", 2: "Competency", 3: "Deep Dive" }

  return (
    <div className="min-h-screen interview-bg-gradient flex items-center justify-center p-4 relative overflow-hidden">
      {/* Confetti */}
      {confetti.map((piece, i) => (
        <div
          key={i}
          className="absolute w-2 h-3 rounded-sm animate-confetti"
          style={{
            left: `${piece.x}%`,
            backgroundColor: piece.color,
            animationDelay: `${piece.delay}s`,
            opacity: 0.8,
          }}
        />
      ))}

      <div className="max-w-lg w-full space-y-6 relative z-10">
        {/* Success Icon */}
        <div className="text-center animate-scale-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white text-black shadow-2xl shadow-white/20 mb-4">
            <Trophy className="h-10 w-10 text-black" />
          </div>
          <h1 className="text-3xl font-bold text-white">Interview Complete!</h1>
          <p className="text-white/50 mt-2 text-sm">
            Great job completing the {levelNames[interview.current_level]} round
          </p>
        </div>

        {/* Stats */}
        {showStats && (
          <Card className="glass-strong border-white/10 shadow-2xl animate-fade-in-up">
            <CardContent className="p-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 rounded-xl bg-white/[0.03]">
                  <div className="flex items-center justify-center mb-2">
                    <BarChart3 className="h-5 w-5 text-white" />
                  </div>
                  <p className="text-2xl font-bold text-white">{answeredQuestions.length}</p>
                  <p className="text-[11px] text-white/40 mt-0.5">
                    Answered
                    {skippedQuestions.length > 0 && (
                      <span className="text-white/60"> ({skippedQuestions.length} skipped)</span>
                    )}
                  </p>
                </div>
                <div className="text-center p-3 rounded-xl bg-white/[0.03]">
                  <div className="flex items-center justify-center mb-2">
                    <Clock className="h-5 w-5 text-white" />
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {totalDuration > 0 ? `${Math.ceil(totalDuration / 60)}m` : "--"}
                  </p>
                  <p className="text-[11px] text-white/40 mt-0.5">Duration</p>
                </div>
                <div className="text-center p-3 rounded-xl bg-white/[0.03]">
                  <div className="flex items-center justify-center mb-2">
                    <Sparkles className="h-5 w-5 text-white" />
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {levelNames[interview.current_level]}
                  </p>
                  <p className="text-[11px] text-white/40 mt-0.5">Level</p>
                </div>
              </div>

              {/* Topics Covered */}
              {interview.topics_covered.length > 0 && (
                <div className="mt-5 pt-4 border-t border-white/5">
                  <p className="text-[11px] text-white/30 uppercase tracking-wider font-medium mb-2">
                    Topics Covered
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {interview.topics_covered.map((topic) => (
                      <span
                        key={topic}
                        className="text-[11px] text-white/50 bg-white/[0.04] px-2.5 py-1 rounded-md border border-white/10"
                      >
                        {topic.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* CTA Buttons */}
        {showCTA && (
          <div className="space-y-3 animate-fade-in-up">
            <Link href={`/session/${sessionId}/results`} className="block">
              <Button
                size="lg"
                className="w-full h-14 bg-white text-black hover:bg-neutral-200 text-base font-bold rounded-xl shadow-xl hover:shadow-2xl transition-all hover:scale-[1.02] cursor-pointer"
              >
                <span className="flex items-center gap-2">
                  View Detailed Results
                  <ArrowRight className="h-5 w-5" />
                </span>
              </Button>
            </Link>

            <Link href="/dashboard" className="block">
              <Button
                variant="ghost"
                size="lg"
                className="w-full h-12 text-white/40 hover:text-white/70 hover:bg-white/5 rounded-xl cursor-pointer"
              >
                Return to Dashboard
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
