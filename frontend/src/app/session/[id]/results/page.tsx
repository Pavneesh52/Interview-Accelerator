"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft, TrendingUp, Award, Target, AlertTriangle, CheckCircle, XCircle, BookOpen, Lightbulb, Brain, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { api } from "@/lib/api"
import { Interview, InterviewEvaluation, QuestionFeedback, PreparationGap, ReadinessLevel } from "@/lib/types"
import { toast } from "@/components/ui/use-toast"
import Link from "next/link"
import { getReadinessColor, getReadinessLabel } from "@/lib/utils"

export default function ResultsPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [interview, setInterview] = useState<Interview | null>(null)
  const [evaluation, setEvaluation] = useState<InterviewEvaluation | null>(null)
  const [loading, setLoading] = useState(true)
  const [generatingEval, setGeneratingEval] = useState(false)

  const fetchResults = async () => {
    setLoading(true)
    try {
      // 1. Fetch session info
      const response = await api.get(`/analysis/sessions/${sessionId}`)
      let interviewData: Interview | null = response.data.interview || null

      // 2. Fallback to direct interview endpoint if not present in session response
      if (!interviewData) {
        try {
          const intRes = await api.get(`/interviews/interviews/session/${sessionId}`)
          interviewData = intRes.data as Interview
        } catch {
          // No interview found yet
        }
      }

      if (interviewData) {
        setInterview(interviewData)

        if (interviewData.evaluation) {
          setEvaluation(interviewData.evaluation)
        } else if (interviewData.status === "completed" || (interviewData.questions && interviewData.questions.some(q => q.answer))) {
          // Auto-trigger evaluation if interview has answers but no evaluation yet
          setGeneratingEval(true)
          try {
            await api.post(`/interviews/interviews/${interviewData.id}/evaluate`)
            const refRes = await api.get(`/interviews/interviews/${interviewData.id}`)
            const updatedInt = refRes.data as Interview
            setInterview(updatedInt)
            setEvaluation(updatedInt.evaluation || null)
          } catch (evalErr) {
            console.error("Failed to generate evaluation:", evalErr)
          } finally {
            setGeneratingEval(false)
          }
        }
      }
    } catch (error) {
      toast({ title: "Error", description: "Failed to load results", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateEvaluation = async () => {
    if (!interview) return
    setGeneratingEval(true)
    try {
      await api.post(`/interviews/interviews/${interview.id}/evaluate`)
      const refRes = await api.get(`/interviews/interviews/${interview.id}`)
      const updatedInt = refRes.data as Interview
      setInterview(updatedInt)
      setEvaluation(updatedInt.evaluation || null)
      toast({ title: "Success", description: "Interview performance report generated!" })
    } catch (error) {
      toast({ title: "Error", description: "Failed to generate performance report", variant: "destructive" })
    } finally {
      setGeneratingEval(false)
    }
  }

  useEffect(() => {
    fetchResults()
  }, [sessionId])

  if (loading || generatingEval) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-muted-foreground font-medium">
          {generatingEval ? "Generating your detailed performance report..." : "Loading interview results..."}
        </p>
      </div>
    )
  }

  if (!interview || !evaluation) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md text-center">
          <CardContent className="py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-yellow-600 mb-4" />
            <h2 className="text-2xl font-bold mb-2">
              {interview ? "Evaluation Report Pending" : "Results Not Available"}
            </h2>
            <p className="text-muted-foreground mb-6">
              {interview
                ? "Your interview session is saved. Click below to generate your detailed performance report."
                : "Complete an interview to see your results."}
            </p>
            <div className="flex flex-col gap-3 justify-center">
              {interview ? (
                <Button onClick={handleGenerateEvaluation} disabled={generatingEval}>
                  {generatingEval ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Brain className="mr-2 h-4 w-4" />}
                  Generate Performance Report
                </Button>
              ) : (
                <Link href={`/session/${sessionId}/interview`}>
                  <Button>Start Interview</Button>
                </Link>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const coreKeys = new Set([
    "role_fit", "role_fit_score",
    "technical_knowledge", "technical_knowledge_score",
    "problem_solving", "problem_solving_score",
    "communication", "communication_score",
    "confidence", "confidence_score",
    "depth_of_understanding", "depth_of_understanding_score",
    "behavioral_fit", "behavioral_fit_score",
  ])

  const coreCompetencies = [
    { label: "Role Fit", score: evaluation.role_fit_score, icon: Target },
    { label: "Technical Knowledge", score: evaluation.technical_knowledge_score, icon: Brain },
    { label: "Problem Solving", score: evaluation.problem_solving_score, icon: Lightbulb },
    { label: "Communication", score: evaluation.communication_score, icon: TrendingUp },
    { label: "Confidence", score: evaluation.confidence_score, icon: Award },
    { label: "Depth of Understanding", score: evaluation.depth_of_understanding_score, icon: Brain },
    { label: "Behavioral Fit", score: evaluation.behavioral_fit_score, icon: Target },
  ].filter(c => c.score !== null && c.score !== undefined)

  // Extra role-specific competencies if provided by evaluation service
  const extraCompetencies = Object.entries(evaluation.competency_scores || {})
    .filter(([key]) => !coreKeys.has(key.toLowerCase().replace(/\s+/g, "_")))
    .map(([key, val]) => ({
      label: key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
      score: val,
      icon: Award,
    }))

  const competencyScores = [...coreCompetencies, ...extraCompetencies]

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="text-xl font-bold">Interview Agent</Link>
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline mb-2 inline-block">
            ← Dashboard
          </Link>
          <h1 className="text-3xl font-bold">Interview Performance Report</h1>
          <p className="text-muted-foreground">Comprehensive evaluation and competency breakdown</p>
        </div>

        {/* Overall Score & Readiness */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-xl">Overall Interview Score: {evaluation.overall_score}/100</CardTitle>
              <CardDescription>Aggregate performance rating across all questions & competencies</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center py-8">
              <div className="relative w-48 h-48 mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="120" cy="120" r="100" stroke="hsl(var(--muted))" strokeWidth="8" fill="none" />
                  <circle
                    cx="120"
                    cy="120"
                    r="100"
                    stroke="hsl(var(--primary))"
                    strokeWidth="8"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={628}
                    strokeDashoffset={628 - (evaluation.overall_score || 0) / 100 * 628}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-5xl font-bold">{evaluation.overall_score}</div>
                    <div className="text-sm font-medium text-muted-foreground">/ 100</div>
                  </div>
                </div>
              </div>
              <Progress value={evaluation.overall_score || 0} className="w-full max-w-xs" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Readiness Assessment</CardTitle>
            </CardHeader>
            <CardContent className="text-center py-8">
              <Badge variant={evaluation.readiness_level?.replace("_", "-") as any} className={`text-lg px-4 py-3 ${getReadinessColor(evaluation.readiness_level || "")}`}>
                {getReadinessLabel(evaluation.readiness_level || "")}
              </Badge>
              <p className="mt-4 text-sm text-muted-foreground">
                {evaluation.readiness_score}/100 readiness score
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Competency Scores */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Competency Scores</CardTitle>
            <CardDescription>Detailed breakdown across key dimensions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {competencyScores.map(({ label, score, icon: Icon }) => (
                <div key={label} className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-5 w-5 text-primary" />
                    <span className="font-medium">{label}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Progress value={score || 0} className="flex-1 h-2" />
                    <span className="font-bold text-lg w-12 text-right">{score}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Tabs for detailed results */}
        <Tabs defaultValue="feedback" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="feedback">Question Feedback</TabsTrigger>
            <TabsTrigger value="strengths">Strengths</TabsTrigger>
            <TabsTrigger value="weaknesses">Weaknesses</TabsTrigger>
            <TabsTrigger value="prep">Preparation Plan</TabsTrigger>
          </TabsList>

          <TabsContent value="feedback" className="space-y-4">
            {evaluation.question_feedbacks?.map((feedback, i) => (
              <Collapsible key={feedback.question_id || i}>
                <CollapsibleTrigger className="bg-muted p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">Q{i + 1}: {feedback.question}</p>
                      <p className="text-sm text-muted-foreground mt-1">{feedback.candidate_answer.substring(0, 100)}...</p>
                    </div>
                    <Badge variant={
                      feedback.assessment === "strong" ? "success" :
                      feedback.assessment === "adequate" ? "warning" : "destructive"
                    }>
                      {feedback.assessment}
                    </Badge>
                  </div>
                </CollapsibleTrigger>
                <CollapsibleContent className="space-y-4 p-4">
                  <div>
                    <h4 className="font-medium mb-2">What Was Good</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {feedback.what_was_good.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">What Could Be Better</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {feedback.what_could_be_better.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Ideal Direction</h4>
                    <p className="text-sm text-muted-foreground">{feedback.ideal_direction}</p>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Competencies: {feedback.competencies_evaluated.join(", ")}</span>
                    <span>Score: {feedback.score}/100</span>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </TabsContent>

          <TabsContent value="strengths" className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {evaluation.strengths?.map((strength, i) => (
                <Badge key={i} variant="success" className="gap-1">
                  <CheckCircle className="h-3 w-3" />
                  {strength}
                </Badge>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="weaknesses" className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {evaluation.weaknesses?.map((weakness, i) => (
                <Badge key={i} variant="destructive" className="gap-1">
                  <XCircle className="h-3 w-3" />
                  {weakness}
                </Badge>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="prep" className="space-y-4">
            {evaluation.preparation_gaps?.map((gap, i) => (
              <Card key={i} className="border-l-4 border-primary">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Priority {gap.priority}: {gap.topic}</CardTitle>
                    <Badge variant="outline">Priority {gap.priority}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-1">
                    {gap.review_items.map((item, idx) => (
                      <li key={idx} className="text-sm">{item}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center mt-8">
          <Link href={`/session/${sessionId}/interview`}>
            <Button variant="outline" size="lg">
              <RotateCcw className="mr-2 h-4 w-4" />
              Retake Interview
            </Button>
          </Link>
          <Link href="/session/new">
            <Button variant="default" size="lg">
              <TrendingUp className="mr-2 h-4 w-4" />
              New Session
            </Button>
          </Link>
        </div>
      </main>
    </div>
  )
}