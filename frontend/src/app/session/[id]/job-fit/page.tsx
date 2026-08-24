"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft, TrendingUp, Target, CheckCircle2, AlertCircle, MinusCircle, XCircle, Award, Sparkles, HelpCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { api } from "@/lib/api"
import { AnalysisSession } from "@/lib/types"
import { toast } from "@/components/ui/use-toast"
import Link from "next/link"
import { getScoreColor } from "@/lib/utils"

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
  const roleTitle = session.jd_analysis?.role_title || "Target Role"

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="text-xl font-bold flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Interview Agent
          </Link>
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

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline mb-2 inline-block">
              ← Dashboard
            </Link>
            <h1 className="text-3xl font-bold">Job Fit Assessment</h1>
            <p className="text-muted-foreground mt-1">
              Role Match Analysis for <span className="font-semibold text-foreground">{roleTitle}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href={`/session/${sessionId}/interview`}>
              <Button variant="default" className="gap-2">
                <TrendingUp className="h-4 w-4" />
                Start AI Interview
              </Button>
            </Link>
          </div>
        </div>

        {/* Hero Score Card */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <Card className="md:col-span-2 border-2 border-primary/10 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-xl">
                <Award className="h-5 w-5 text-primary" />
                Current Role Fit Assessment
              </CardTitle>
              <CardDescription>
                Quantitative and semantic match score against role expectations
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col sm:flex-row items-center justify-around py-6 gap-6">
              <div className="relative w-44 h-44 flex-shrink-0">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="88"
                    cy="88"
                    r="72"
                    stroke="hsl(var(--muted))"
                    strokeWidth="10"
                    fill="none"
                  />
                  <circle
                    cx="88"
                    cy="88"
                    r="72"
                    stroke="hsl(var(--primary))"
                    strokeWidth="10"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={452}
                    strokeDashoffset={452 - (jobFit.score / 100) * 452}
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <span className="text-sm font-medium text-muted-foreground block">Job Fit</span>
                    <span className="text-4xl font-extrabold tracking-tight">{jobFit.score}%</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4 text-center sm:text-left flex-1 max-w-sm">
                <div>
                  <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Match Classification</span>
                  <div className="mt-1">
                    <Badge variant={
                      jobFit.score >= 85 ? "success" :
                      jobFit.score >= 70 ? "default" :
                      jobFit.score >= 50 ? "warning" : "destructive"
                    } className="text-base px-4 py-1 font-bold">
                      {jobFit.rating}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-muted-foreground font-medium">
                    <span>Role Alignment</span>
                    <span>{jobFit.score}/100</span>
                  </div>
                  <Progress value={jobFit.score} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Scoring Methodology Card */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <HelpCircle className="h-4 w-4 text-muted-foreground" />
                Scoring Methodology
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs leading-relaxed text-muted-foreground">
              <p>{jobFit.methodology || "Evaluated across required technical skills, project depth, preferred qualifications, and gaps."}</p>
              
              {jobFit.skill_match_details && (
                <div className="pt-2 border-t space-y-2">
                  <p className="font-semibold text-foreground">Match Metrics:</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded bg-muted/50">
                      <span className="block text-muted-foreground">Required Skills</span>
                      <span className="font-bold text-foreground font-mono">{(jobFit.skill_match_details as any).matched_required || 0}/{(jobFit.skill_match_details as any).total_required || 0} ({(jobFit.skill_match_details as any).required_match_pct || 0}%)</span>
                    </div>
                    <div className="p-2 rounded bg-muted/50">
                      <span className="block text-muted-foreground">Preferred Skills</span>
                      <span className="font-bold text-foreground font-mono">{(jobFit.skill_match_details as any).matched_preferred || 0}/{(jobFit.skill_match_details as any).total_preferred || 0} ({(jobFit.skill_match_details as any).preferred_match_pct || 0}%)</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 3-Tier Match Breakdown Grid */}
        <h2 className="text-xl font-bold mb-4">Competency & Skill Breakdown</h2>
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          {/* Strong Match */}
          <Card className="border-t-4 border-t-green-500 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-green-700 dark:text-green-400">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Strong Match
              </CardTitle>
              <CardDescription>
                Skills & competencies directly verified in candidate profile
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jobFit.strong_matches.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No strong matches identified</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {jobFit.strong_matches.map((skill, idx) => (
                    <Badge key={idx} variant="success" className="py-1 px-3 text-xs font-medium gap-1.5 shadow-2xs">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Partial Match */}
          <Card className="border-t-4 border-t-yellow-500 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-yellow-700 dark:text-yellow-400">
                <MinusCircle className="h-5 w-5 text-yellow-600" />
                Partial Match
              </CardTitle>
              <CardDescription>
                Adjacent experience, foundational, or non-production level
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jobFit.partial_matches.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No partial matches identified</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {jobFit.partial_matches.map((skill, idx) => (
                    <Badge key={idx} variant="warning" className="py-1 px-3 text-xs font-medium gap-1.5 shadow-2xs">
                      <MinusCircle className="h-3.5 w-3.5" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Missing / Weak */}
          <Card className="border-t-4 border-t-red-500 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-red-700 dark:text-red-400">
                <XCircle className="h-5 w-5 text-red-600" />
                Missing / Weak
              </CardTitle>
              <CardDescription>
                Crucial requirements missing or needing interview clarification
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jobFit.missing_weak.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No skill gaps identified</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {jobFit.missing_weak.map((skill, idx) => (
                    <Badge key={idx} variant="destructive" className="py-1 px-3 text-xs font-medium gap-1.5 shadow-2xs">
                      <XCircle className="h-3.5 w-3.5" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Formatted Text Response View */}

        <Card className="mb-8 border shadow-xs">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                Formatted Analysis Response
              </CardTitle>
              <CardDescription>Structured plain text output format</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const text = jobFit.formatted_summary || [
                  `Job Fit: ${jobFit.score}%`,
                  jobFit.rating,
                  ...jobFit.strong_matches,
                  "Partial Match",
                  ...jobFit.partial_matches,
                  "Missing / Weak",
                  ...jobFit.missing_weak,
                ].join("\n");
                navigator.clipboard.writeText(text);
                toast({ title: "Copied to Clipboard", description: "Formatted analysis text copied successfully." });
              }}
            >
              Copy Text
            </Button>
          </CardHeader>
          <CardContent>
            <pre className="p-4 bg-muted font-mono text-sm rounded-lg overflow-x-auto whitespace-pre-wrap leading-relaxed">
{jobFit.formatted_summary || [
  `Job Fit: ${jobFit.score}%`,
  jobFit.rating,
  ...jobFit.strong_matches,
  "Partial Match",
  ...jobFit.partial_matches,
  "Missing / Weak",
  ...jobFit.missing_weak,
].join("\n")}
            </pre>
          </CardContent>
        </Card>

        {/* Action Callouts */}
        <Card className="bg-muted/40 border shadow-xs">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Recommended Action</CardTitle>
            <CardDescription>Use these insights to prepare for the targeted mock interview</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <Link href={`/session/${sessionId}/interview`}>
              <Button variant="default" className="w-full h-auto p-4 flex items-center justify-between" size="lg">
                <div className="text-left">
                  <p className="font-semibold text-base">Launch Adaptive Mock Interview</p>
                  <p className="text-xs text-primary-foreground/80">Simulate questions tailored to your gaps and strengths</p>
                </div>
                <TrendingUp className="h-5 w-5 ml-2 flex-shrink-0" />
              </Button>
            </Link>

            <Link href={`/session/${sessionId}/results`}>
              <Button variant="outline" className="w-full h-auto p-4 flex items-center justify-between" size="lg">
                <div className="text-left">
                  <p className="font-semibold text-base">View Detailed Analysis</p>
                  <p className="text-xs text-muted-foreground">Deep dive into resume analysis and question plan</p>
                </div>
                <Target className="h-5 w-5 ml-2 flex-shrink-0" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}