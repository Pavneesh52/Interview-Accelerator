"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft, TrendingUp, Target, CheckCircle, AlertCircle, MinusCircle, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"
import { AnalysisSession, JobFitAssessment } from "@/lib/types"
import { toast } from "@/components/ui/use-toast"
import Link from "next/link"
import { getScoreColor, getReadinessColor, getReadinessLabel } from "@/lib/utils"

export default function JobFitPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [session, setSession] = useState<AnalysisSession | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchSession = async () => {
    try {
      const response = await api.get(`/analysis/sessions/${sessionId}`)
      setSession(response.data)
    } catch (error) {
      toast({ title: "Error", description: "Failed to load session", variant: "destructive" })
      router.push("/dashboard")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSession()
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!session || !session.job_fit) return null

  const jobFit = session.job_fit

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
          <h1 className="text-3xl font-bold">Job Fit Assessment</h1>
          <p className="text-muted-foreground">
            How well your resume matches the job requirements
          </p>
        </div>

        {/* Overall Score */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Overall Job Fit Score</CardTitle>
              <CardDescription>Weighted assessment across all criteria</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center py-8">
              <div className="relative w-48 h-48 mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="120"
                    cy="120"
                    r="100"
                    stroke="hsl(var(--muted))"
                    strokeWidth="8"
                    fill="none"
                  />
                  <circle
                    cx="120"
                    cy="120"
                    r="100"
                    stroke={`hsl(var(--primary))`}
                    strokeWidth="8"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={628}
                    strokeDashoffset={628 - (jobFit.score / 100) * 628}
                    className="transition-all duration-1000"
                    style={{ strokeDasharray: 628, strokeDashoffset: 628 - (jobFit.score / 100) * 628 }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-5xl font-bold">{jobFit.score}%</div>
                    <div className={`text-sm font-medium ${getScoreColor(jobFit.score)} px-3 py-1 rounded-full`}>
                      {jobFit.rating}
                    </div>
                  </div>
                </div>
              </div>
              <Progress value={jobFit.score} className="w-full max-w-xs" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Methodology</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p className="text-muted-foreground">{jobFit.methodology}</p>
              {jobFit.skill_match_details && (
                <div className="space-y-2">
                  <p className="font-medium">Skill Match Details:</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Required Match: </span>
                      <span className="font-medium">{(jobFit.skill_match_details as any).required_match_pct}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Preferred Match: </span>
                      <span className="font-medium">{(jobFit.skill_match_details as any).preferred_match_pct}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Matched Required: </span>
                      <span className="font-medium">{(jobFit.skill_match_details as any).matched_required}/{(jobFit.skill_match_details as any).total_required}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Matched Preferred: </span>
                      <span className="font-medium">{(jobFit.skill_match_details as any).matched_preferred}/{(jobFit.skill_match_details as any).total_preferred}</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Breakdown */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Strong Matches
              </CardTitle>
              <CardDescription>{jobFit.strong_matches.length} items</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {jobFit.strong_matches.length === 0 ? (
                  <span className="text-muted-foreground text-sm">No strong matches</span>
                ) : (
                  jobFit.strong_matches.map((skill) => (
                    <Badge key={skill} variant="success" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      {skill}
                    </Badge>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MinusCircle className="h-5 w-5 text-yellow-600" />
                Partial Matches
              </CardTitle>
              <CardDescription>{jobFit.partial_matches.length} items</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {jobFit.partial_matches.length === 0 ? (
                  <span className="text-muted-foreground text-sm">No partial matches</span>
                ) : (
                  jobFit.partial_matches.map((skill) => (
                    <Badge key={skill} variant="warning" className="gap-1">
                      <MinusCircle className="h-3 w-3" />
                      {skill}
                    </Badge>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-600" />
                Missing / Weak
              </CardTitle>
              <CardDescription>{jobFit.missing_weak.length} items</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {jobFit.missing_weak.length === 0 ? (
                  <span className="text-muted-foreground text-sm">No gaps identified</span>
                ) : (
                  jobFit.missing_weak.map((skill) => (
                    <Badge key={skill} variant="destructive" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      {skill}
                    </Badge>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>Recommended actions based on your job fit assessment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Link href={`/session/${sessionId}/interview`}>
                <Button variant="default" className="w-full h-auto p-6 text-left" size="lg">
                  <TrendingUp className="mr-2 h-5 w-5" />
                  <div>
                    <p className="font-semibold">Start AI Interview</p>
                    <p className="text-sm text-muted-foreground">Practice with personalized questions</p>
                  </div>
                </Button>
              </Link>
              
              <Link href={`/session/${sessionId}/results`}>
                <Button variant="outline" className="w-full h-auto p-6 text-left" size="lg">
                  <Target className="mr-2 h-5 w-5" />
                  <div>
                    <p className="font-semibold">View Full Report</p>
                    <p className="text-sm text-muted-foreground">Detailed analysis and preparation plan</p>
                  </div>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}