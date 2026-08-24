"use client"

import { Interview, InterviewLevel } from "@/lib/types"

interface InterviewProgressProps {
  interview: Interview
}

export function InterviewProgress({ interview }: InterviewProgressProps) {
  const answered = interview.questions.filter((q) => q.answer).length
  const total = interview.total_questions
  const progress = total > 0 ? (answered / total) * 100 : 0

  const levelNames: Record<number, string> = { 1: "Screening", 2: "Competency", 3: "Deep Dive" }
  const levelName = levelNames[interview.current_level] || "Unknown"

  // SVG progress ring parameters
  const radius = 38
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference - (progress / 100) * circumference

  const getLevelColor = (level: InterviewLevel) => {
    switch (level) {
      case 1: return { stroke: "#6366f1", bg: "text-indigo-400" }
      case 2: return { stroke: "#f59e0b", bg: "text-amber-400" }
      case 3: return { stroke: "#ef4444", bg: "text-red-400" }
      default: return { stroke: "#6366f1", bg: "text-indigo-400" }
    }
  }

  const colors = getLevelColor(interview.current_level)

  return (
    <div className="flex items-center gap-4">
      {/* Progress Ring */}
      <div className="relative w-16 h-16 shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 84 84">
          {/* Background ring */}
          <circle
            cx="42"
            cy="42"
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="4"
          />
          {/* Progress ring */}
          <circle
            cx="42"
            cy="42"
            r={radius}
            fill="none"
            stroke={colors.stroke}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="transition-all duration-700 ease-out"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-sm font-bold ${colors.bg}`}>{answered}</span>
          <span className="text-[10px] text-white/30">/{total}</span>
        </div>
      </div>

      {/* Info */}
      <div className="min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-semibold ${colors.bg}`}>Level {interview.current_level}</span>
          <span className="text-white/20">·</span>
          <span className="text-xs text-white/50">{levelName}</span>
        </div>

        {/* Question dots */}
        <div className="flex items-center gap-[3px] flex-wrap max-w-[180px]">
          {interview.questions.map((q, i) => (
            <div
              key={q.id}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                q.answer
                  ? q.answer.transcript === "[SKIPPED]"
                    ? "bg-amber-400/60"
                    : "bg-emerald-400"
                  : i === interview.current_question_index
                  ? `bg-white animate-pulse`
                  : "bg-white/15"
              }`}
              title={`Q${i + 1}: ${q.answer ? (q.answer.transcript === "[SKIPPED]" ? "Skipped" : "Answered") : i === interview.current_question_index ? "Current" : "Upcoming"}`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
