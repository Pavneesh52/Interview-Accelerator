"use client"

import { useEffect, useState } from "react"
import { Mic, MicOff, Volume2, CheckCircle2, Clock, Shield, Sparkles, ChevronRight, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { InterviewerIntro, InterviewLevel } from "@/lib/types"

interface InterviewLobbyProps {
  intro: InterviewerIntro | null
  level: InterviewLevel
  loading: boolean
  onBegin: () => void
}

export function InterviewLobby({ intro, level, loading, onBegin }: InterviewLobbyProps) {
  const [micReady, setMicReady] = useState(false)
  const [micError, setMicError] = useState<string | null>(null)
  const [speakerReady, setSpeakerReady] = useState(false)
  const [showTips, setShowTips] = useState(false)

  useEffect(() => {
    // Check mic permission
    navigator.mediaDevices
      ?.getUserMedia({ audio: true })
      .then((stream) => {
        stream.getTracks().forEach((t) => t.stop())
        setMicReady(true)
      })
      .catch(() => {
        setMicError("Microphone access denied. You can still type your answers.")
      })

    // Check speech synthesis
    setSpeakerReady("speechSynthesis" in window)

    // Animate tips in after short delay
    const timer = setTimeout(() => setShowTips(true), 800)
    return () => clearTimeout(timer)
  }, [])

  const levelConfig = {
    1: {
      name: "Screening",
      description: "First-round conversation about your background and fit",
      gradient: "bg-white text-black",
      bgGlow: "bg-white/5",
      icon: "🎯",
    },
    2: {
      name: "Competency",
      description: "Technical depth and problem-solving assessment",
      gradient: "bg-white text-black",
      bgGlow: "bg-white/5",
      icon: "⚡",
    },
    3: {
      name: "Deep Dive",
      description: "Advanced reasoning and system design evaluation",
      gradient: "bg-white text-black",
      bgGlow: "bg-white/5",
      icon: "🔬",
    },
  }

  const config = levelConfig[level] || levelConfig[1]

  return (
    <div className="min-h-screen interview-bg-gradient flex items-center justify-center p-4">
      <div className="max-w-2xl w-full space-y-6 animate-scale-in">
        {/* Level Badge */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-white/20 bg-white/10 text-white text-sm font-semibold shadow-lg">
            <span className="text-lg">{config.icon}</span>
            Level {level}: {config.name}
          </div>
        </div>

        {/* Main Card */}
        <Card className="glass-strong border-white/10 shadow-2xl overflow-hidden text-white rounded-3xl">
          <CardContent className="p-8 space-y-8">
            {/* Interviewer Intro */}
            {intro ? (
              <div className="space-y-4 animate-fade-in">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-white text-black font-extrabold text-xl flex items-center justify-center shadow-lg border border-white/20">
                    {intro.interviewer_name.charAt(0)}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">{intro.interviewer_name}</h2>
                    <p className="text-sm text-white/60">{intro.interviewer_title}</p>
                  </div>
                </div>
                <p className="text-white/80 leading-relaxed text-[15px]">
                  {intro.greeting}
                </p>
              </div>
            ) : loading ? (
              <div className="flex items-center gap-3 text-white/60">
                <div className="w-10 h-10 rounded-full bg-white/10 animate-pulse" />
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-white/10 rounded animate-pulse w-1/3" />
                  <div className="h-3 bg-white/10 rounded animate-pulse w-2/3" />
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <h2 className="text-xl font-bold text-white">Interview Simulator</h2>
                <p className="text-white/60 mt-1">{config.description}</p>
              </div>
            )}

            {/* Focus Areas */}
            {intro && intro.focus_areas && (
              <div className="space-y-3 animate-fade-in">
                <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider">What we&apos;ll cover</h3>
                <div className="flex flex-wrap gap-2">
                  {intro.focus_areas.map((area) => (
                    <Badge key={area} variant="outline" className="bg-white/5 border-white/15 text-white/80 text-xs px-3 py-1.5">
                      {area}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Device Checks */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider">Equipment Check</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className={`flex items-center gap-3 p-3 rounded-xl ${micReady ? "bg-white/10 border border-white/20" : "bg-white/5 border border-white/10"}`}>
                  {micReady ? (
                    <CheckCircle2 className="h-5 w-5 text-white shrink-0" />
                  ) : (
                    <Mic className="h-5 w-5 text-white/40 shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-white/80">Microphone</p>
                    <p className="text-xs text-white/40">
                      {micReady ? "Ready" : micError ? "Optional" : "Checking..."}
                    </p>
                  </div>
                </div>
                <div className={`flex items-center gap-3 p-3 rounded-xl ${speakerReady ? "bg-white/10 border border-white/20" : "bg-white/5 border border-white/10"}`}>
                  {speakerReady ? (
                    <CheckCircle2 className="h-5 w-5 text-white shrink-0" />
                  ) : (
                    <Volume2 className="h-5 w-5 text-white/40 shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-white/80">Speaker</p>
                    <p className="text-xs text-white/40">{speakerReady ? "Ready" : "Unavailable"}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Duration & Info */}
            <div className="flex items-center justify-center gap-6 text-white/50 text-sm">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span>~{intro?.estimated_duration_minutes || 15} minutes</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                <span>Private & secure</span>
              </div>
            </div>

            {/* Tips */}
            {showTips && intro && intro.tips && (
              <div className="space-y-2 animate-fade-in">
                <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="h-3.5 w-3.5" />
                  Tips for success
                </h3>
                <ul className="space-y-1.5">
                  {intro.tips.slice(0, 3).map((tip, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                      <span className="text-white mt-0.5">•</span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Begin Button */}
            <Button
              onClick={onBegin}
              disabled={loading}
              size="lg"
              className="w-full h-14 bg-white text-black hover:bg-neutral-200 text-lg font-bold rounded-xl shadow-xl transition-all duration-300 hover:shadow-2xl hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 cursor-pointer"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Preparing...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Begin Interview
                  <ChevronRight className="h-5 w-5" />
                </span>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <p className="text-center text-xs text-white/30">
          This is a practice simulation. Your responses are private and used only for feedback.
        </p>
      </div>
    </div>
  )
}
