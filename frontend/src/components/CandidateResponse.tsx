"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Mic, MicOff, Send, Keyboard, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SpeechRecognitionEvent extends Event {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionResultList {
  length: number
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start: () => void
  stop: () => void
  abort: () => void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: Event) => void) | null
  onend: (() => void) | null
}

declare global {
  interface Window {
    webkitSpeechRecognition: new () => SpeechRecognition
    SpeechRecognition: new () => SpeechRecognition
  }
}

interface CandidateResponseProps {
  onSubmit: (transcript: string, durationSeconds: number) => void
  disabled: boolean
  questionId: string | null
}

export function CandidateResponse({ onSubmit, disabled, questionId }: CandidateResponseProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [interimText, setInterimText] = useState("")
  const [useTextMode, setUseTextMode] = useState(false)
  const [textInput, setTextInput] = useState("")
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const startTimeRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const hasRecognition = useRef(false)

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognitionAPI) {
      hasRecognition.current = true
    }
  }, [])

  // Reset state when question changes
  useEffect(() => {
    setTranscript("")
    setInterimText("")
    setTextInput("")
    setIsRecording(false)
    setRecordingDuration(0)
    setSubmitting(false)
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [questionId])

  const startRecording = useCallback(() => {
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognitionAPI) {
      setUseTextMode(true)
      return
    }

    const recognition = new SpeechRecognitionAPI() as SpeechRecognition
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = "en-US"

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = ""
      let interim = ""
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      if (finalTranscript) {
        setTranscript((prev) => (prev ? prev + " " + finalTranscript : finalTranscript))
      }
      setInterimText(interim)
    }

    recognition.onerror = () => {
      setIsRecording(false)
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }

    recognition.onend = () => {
      setIsRecording(false)
      setInterimText("")
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }

    recognitionRef.current = recognition
    recognition.start()
    setIsRecording(true)
    startTimeRef.current = Date.now()
    setRecordingDuration(0)

    timerRef.current = setInterval(() => {
      setRecordingDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
  }, [])

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setIsRecording(false)
    setInterimText("")
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const handleSubmit = async () => {
    const answer = useTextMode ? textInput.trim() : transcript.trim()
    if (!answer) return

    setSubmitting(true)
    const duration = useTextMode ? 0 : recordingDuration
    await onSubmit(answer, duration)
    setSubmitting(false)
  }

  const handleReset = () => {
    setTranscript("")
    setInterimText("")
    setTextInput("")
    setRecordingDuration(0)
  }

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, "0")}`
  }

  const currentAnswer = useTextMode ? textInput : transcript
  const wordCount = currentAnswer.trim().split(/\s+/).filter(Boolean).length

  return (
    <div className="flex flex-col h-full">
      {/* Mode Toggle */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white/50 text-xs uppercase tracking-wider font-semibold">Your Response</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setUseTextMode(!useTextMode)}
          className="text-white/40 hover:text-white/70 hover:bg-white/5 text-xs h-7 px-2 cursor-pointer"
        >
          {useTextMode ? <Mic className="h-3.5 w-3.5 mr-1.5" /> : <Keyboard className="h-3.5 w-3.5 mr-1.5" />}
          {useTextMode ? "Voice mode" : "Type mode"}
        </Button>
      </div>

      {/* Response Area */}
      <div className="flex-1 flex flex-col gap-4">
        {useTextMode ? (
          /* Text Input Mode */
          <div className="flex-1 flex flex-col">
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type your answer here..."
              disabled={disabled || submitting}
              className="flex-1 w-full p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/20 resize-none focus:outline-none focus:border-indigo-500/40 focus:ring-1 focus:ring-indigo-500/20 transition-all text-sm leading-relaxed min-h-[200px]"
            />
          </div>
        ) : (
          /* Voice Mode */
          <div className="flex-1 flex flex-col items-center justify-center">
            {/* Mic Button */}
            <div className="relative mb-6">
              {/* Ripple rings when recording */}
              {isRecording && (
                <>
                  <div className="absolute inset-0 rounded-full bg-red-500/20 animate-mic-ripple" />
                  <div className="absolute inset-0 rounded-full bg-red-500/15 animate-mic-ripple-delayed" />
                  <div className="absolute inset-0 rounded-full bg-red-500/10 animate-mic-ripple-delayed-2" />
                </>
              )}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={disabled || submitting}
                className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
                  isRecording
                    ? "bg-neutral-100 text-black animate-mic-pulse shadow-xl shadow-white/20"
                    : "bg-white hover:bg-neutral-200 text-black shadow-lg shadow-white/10 hover:shadow-xl hover:scale-105"
                } disabled:opacity-50 disabled:hover:scale-100`}
              >
                {isRecording ? (
                  <MicOff className="h-8 w-8 text-black" />
                ) : (
                  <Mic className="h-8 w-8 text-black" />
                )}
              </button>
            </div>

            {/* Recording Info */}
            <div className="text-center mb-4">
              {isRecording ? (
                <div className="space-y-1">
                  <p className="text-neutral-200 text-sm font-medium flex items-center justify-center gap-2">
                    <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    Recording — {formatDuration(recordingDuration)}
                  </p>
                  <p className="text-white/30 text-xs">Click to stop</p>
                </div>
              ) : (
                <p className="text-white/30 text-sm">
                  {transcript ? "Click to continue recording" : "Click microphone to start"}
                </p>
              )}
            </div>

            {/* Transcript Display */}
            <div className="w-full p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06] min-h-[120px] max-h-[200px] overflow-y-auto interview-scroll">
              {transcript || interimText ? (
                <p className="text-white/80 text-sm leading-relaxed">
                  {transcript}
                  {interimText && (
                    <span className="text-white/30 italic"> {interimText}</span>
                  )}
                </p>
              ) : (
                <p className="text-white/15 text-sm text-center pt-8">
                  Your answer will appear here as you speak...
                </p>
              )}
            </div>
          </div>
        )}

        {/* Stats & Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-white/30">
            {wordCount > 0 && <span>{wordCount} words</span>}
            {!useTextMode && recordingDuration > 0 && (
              <span>{formatDuration(recordingDuration)}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {currentAnswer && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-white/30 hover:text-white/60 hover:bg-white/5 h-9 px-3 cursor-pointer"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                Reset
              </Button>
            )}
            <Button
              onClick={handleSubmit}
              disabled={!currentAnswer.trim() || disabled || submitting}
              size="sm"
              className="bg-white text-black hover:bg-neutral-200 h-9 px-5 rounded-xl font-medium shadow-lg disabled:opacity-40 disabled:shadow-none transition-all cursor-pointer"
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Submitting
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <Send className="h-3.5 w-3.5" />
                  Submit
                </span>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
