"use client"

import * as React from "react"
import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft, Mic, MicOff, Volume2, VolumeX, Send, RotateCcw, ChevronLeft, ChevronRight, Pause, Play, SkipBack, SkipForward } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { api } from "@/lib/api"
import { Interview, InterviewQuestion, InterviewAnswer, InterviewLevel, QuestionType, DifficultyLevel } from "@/lib/types"
import { toast } from "@/components/ui/use-toast"
import Link from "next/link"

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
  onresult: (event: SpeechRecognitionEvent) => void
  onerror: (event: Event) => void
}

declare global {
  interface Window {
    webkitSpeechRecognition: new () => SpeechRecognition
  }
}

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [interview, setInterview] = useState<Interview | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentAnswer, setCurrentAnswer] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null)

  const fetchInterview = async () => {
    try {
      const response = await api.get(`/analysis/sessions/${sessionId}`)
      if (response.data.interview) {
        setInterview(response.data.interview)
      } else {
        // Start interview
        const startResponse = await api.post("/interviews/start", { session_id: sessionId })
        setInterview(startResponse.data)
      }
    } catch (error) {
      toast({ title: "Error", description: "Failed to load interview", variant: "destructive" })
      router.push("/dashboard")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInterview()
    
    // Initialize Speech Recognition
    if ("webkitSpeechRecognition" in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition
      const recog = new SpeechRecognition()
      recog.continuous = true
      recog.interimResults = true
      recog.lang = "en-US"
      
      recog.onresult = (event: any) => {
        let finalTranscript = ""
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript
          }
        }
        if (finalTranscript) {
          setTranscript(prev => prev + " " + finalTranscript)
        }
      }
      
      recog.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error)
      }
      
      setRecognition(recog)
    }
  }, [sessionId])

  const currentQuestion = interview?.questions?.[interview?.current_question_index || 0]
  const progress = interview ? ((interview.current_question_index + 1) / interview.total_questions) * 100 : 0

  const handleStartRecording = () => {
    if (recognition && !isRecording) {
      setTranscript("")
      recognition.start()
      setIsRecording(true)
    }
  }

  const handleStopRecording = () => {
    if (recognition && isRecording) {
      recognition.stop()
      setIsRecording(false)
      setCurrentAnswer(transcript)
    }
  }

  const handleSubmitAnswer = async () => {
    if (!currentQuestion || !currentAnswer.trim()) return
    
    try {
      await api.post(`/interviews/questions/${currentQuestion.id}/answer`, {
        transcript: currentAnswer,
        audio_url: null,
        video_url: null,
        duration_seconds: 0
      })
      
      // Get next question (handles follow-ups)
      const nextResponse = await api.post(`/interviews/${interview.id}/next-question`)
      setInterview(prev => {
        if (!prev) return prev
        return {
          ...prev,
          questions: [...prev.questions, nextResponse.data],
          current_question_index: prev.current_question_index + 1,
          total_questions: prev.total_questions + (nextResponse.data.is_follow_up ? 1 : 0)
        }
      })
      setCurrentAnswer("")
      setTranscript("")
    } catch (error: any) {
      if (error.response?.status === 400 && error.response?.data?.detail === "Interview completed") {
        // Interview completed, refresh to get evaluation
        const response = await api.get(`/analysis/sessions/${sessionId}`)
        setInterview(response.data.interview)
      } else {
        toast({ title: "Error", description: "Failed to submit answer", variant: "destructive" })
      }
    }
  }

  const speakText = (text: string) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1
      utterance.pitch = 1
      speechSynthesis.speak(utterance)
    }
  }

  const handleSpeakQuestion = () => {
    if (currentQuestion) {
      speakText(currentQuestion.question_text)
    }
  }

  const getLevelLabel = (level: InterviewLevel) => {
    switch (level) {
      case 1: return "Screening"
      case 2: return "Competency"
      case 3: return "Deep Dive"
      default: return "Unknown"
    }
  }

  const getLevelColor = (level: InterviewLevel) => {
    switch (level) {
      case 1: return "bg-blue-100 text-blue-800"
      case 2: return "bg-yellow-100 text-yellow-800"
      case 3: return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!interview) return null

  const isComplete = interview.status === "completed"

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="font-bold">Interview Agent</h1>
              <p className="text-xs text-muted-foreground">Session: {sessionId.slice(0, 8)}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Badge className={getLevelColor(interview.current_level)}>
              Level {interview.current_level}: {getLevelLabel(interview.current_level)}
            </Badge>
            <div className="hidden sm:block w-64">
              <Progress value={progress} className="h-2" />
            </div>
            <span className="text-sm font-medium">{interview.current_question_index + 1} / {interview.total_questions}</span>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-6 flex flex-col">
        {isComplete ? (
          <div className="flex-1 flex items-center justify-center">
            <Card className="max-w-md w-full text-center">
              <CardContent className="py-12">
                <div className="text-green-600 mb-4">
                  <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold mb-2">Interview Complete!</h2>
                <p className="text-muted-foreground mb-6">Great job! Your interview has been completed and evaluated.</p>
                <Link href={`/session/${sessionId}/results`}>
                  <Button size="lg">View Results</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        ) : currentQuestion ? (
          <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
            {/* Question Card */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <Badge variant="outline" className="mb-2">
                      {currentQuestion.question_type.replace("_", " ").toUpperCase()}
                    </Badge>
                    <CardTitle className="text-xl">{currentQuestion.question_text}</CardTitle>
                    <CardDescription>
                      Difficulty: {currentQuestion.difficulty} • 
                      Competencies: {currentQuestion.expected_competencies.join(", ")}
                    </CardDescription>
                  </div>
                  <Button variant="outline" onClick={handleSpeakQuestion} disabled={isMuted}>
                    {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {currentQuestion.is_follow_up && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                    <strong>Follow-up Question:</strong> This question was generated based on your previous answer.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Answer Section */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Your Answer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Voice Controls */}
                <div className="flex items-center gap-4 p-4 bg-muted rounded-lg">
                  <Button
                    onClick={isRecording ? handleStopRecording : handleStartRecording}
                    disabled={!recognition}
                    size="lg"
                    variant={isRecording ? "destructive" : "default"}
                    className="w-16 h-16 rounded-full"
                  >
                    {isRecording ? (
                      <MicOff className="h-8 w-8" />
                    ) : (
                      <Mic className="h-8 w-8" />
                    )}
                  </Button>
                  
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        {isRecording ? "Listening..." : "Click microphone to start recording"}
                      </span>
                      {isRecording && <span className="text-sm text-red-600 animate-pulse">● REC</span>}
                    </div>
                    <div className="h-20 border rounded p-2 bg-background overflow-y-auto font-mono text-sm">
                      {transcript || currentAnswer || <span className="text-muted-foreground">Your transcript will appear here...</span>}
                    </div>
                  </div>
                </div>

                {/* Manual Text Input */}
                <div>
                  <label className="block text-sm font-medium mb-2">Or type your answer:</label>
                  <textarea
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    placeholder="Type your answer here..."
                    className="w-full min-h-[100px] p-3 border rounded-lg bg-background"
                    rows={4}
                  />
                </div>

                <Button onClick={handleSubmitAnswer} disabled={!currentAnswer.trim()} className="w-full" size="lg">
                  <Send className="mr-2 h-4 w-4" />
                  Submit Answer
                </Button>
              </CardContent>
            </Card>

            {/* Previous Q&A */}
            {interview.questions && interview.questions.length > 0 && (
              <Collapsible className="mb-6">
                <CollapsibleTrigger>
                  Previous Questions & Answers ({interview.current_question_index})
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="space-y-4 mt-4">
                    {interview.questions
                      .slice(0, interview.current_question_index)
                      .map((q, i) => (
                        <Card key={q.id} className="bg-muted/50">
                          <CardContent className="pt-4">
                            <p className="font-medium mb-2">Q{i + 1}: {q.question_text}</p>
                            {q.answer && (
                              <p className="text-muted-foreground text-sm">A: {q.answer.transcript}</p>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <Card className="max-w-md w-full text-center">
              <CardContent className="py-12">
                <Loader2 className="mx-auto h-12 w-12 text-primary animate-spin mb-4" />
                <h2 className="text-2xl font-bold mb-2">Preparing Interview...</h2>
                <p className="text-muted-foreground">Generating personalized questions based on your profile.</p>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}