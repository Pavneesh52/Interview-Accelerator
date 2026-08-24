"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft, Brain, Target, Lightbulb, FileText, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"
import { AnalysisSession, JDAnalysis, TechnicalCompetency, BehavioralCompetency } from "@/lib/types"
import { toast } from "@/components/ui/use-toast"
import Link from "next/link"

export default function AnalysisPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [session, setSession] = useState<AnalysisSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)

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

  const runAnalysis = async () => {
    setAnalyzing(true)
    try {
      await api.post(`/analysis/sessions/${sessionId}/analyze`)
      toast({ title: "Analysis started", description: "This may take a minute..." })
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const response = await api.get(`/analysis/sessions/${sessionId}`)
          if (response.data.status === "completed") {
            setSession(response.data)
            clearInterval(poll)
            setAnalyzing(false)
            toast({ title: "Analysis complete", description: "View results below" })
          } else if (response.data.status === "failed") {
            clearInterval(poll)
            setAnalyzing(false)
            toast({ title: "Analysis failed", description: "Please try again", variant: "destructive" })
          }
        } catch {
          clearInterval(poll)
          setAnalyzing(false)
        }
      }, 3000)
    } catch (error) {
      setAnalyzing(false)
      toast({ title: "Error", description: "Failed to start analysis", variant: "destructive" })
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

  if (!session) return null

  const jdAnalysis = session.jd_analysis

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
            {session.status === "completed" && (
              <div className="flex items-center gap-2">
                <Link href={`/session/${sessionId}/job-fit`}>
                  <Button variant="outline" size="sm">
                    Job Fit Assessment
                  </Button>
                </Link>
                <Link href={`/session/${sessionId}/interview`}>
                  <Button variant="default" size="sm" className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white">
                    <Brain className="mr-2 h-4 w-4" />
                    Start AI Interview
                  </Button>
                </Link>
              </div>
            )}
            {session.status !== "completed" && (
              <Button onClick={runAnalysis} disabled={analyzing} size="sm">
                {analyzing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="mr-2 h-4 w-4" />
                    Run Analysis
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline mb-2 inline-block">
            ← Dashboard
          </Link>
          <h1 className="text-3xl font-bold">Role Analysis</h1>
          <p className="text-muted-foreground">
            AI-powered analysis of the job description
          </p>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <Badge variant={
            session.status === "completed" ? "success" :
            session.status === "processing" ? "info" :
            session.status === "failed" ? "destructive" : "secondary"
          } className="text-lg px-4 py-2">
            {session.status === "completed" && <CheckCircle className="mr-2 h-4 w-4" />}
            {session.status === "processing" && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {session.status === "failed" && <AlertCircle className="mr-2 h-4 w-4" />}
            {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
          </Badge>
        </div>

        {session.status === "completed" && jdAnalysis && (
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="skills">Skills & Competencies</TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="raw">Raw Data</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{jdAnalysis.role_title}</CardTitle>
                  <CardDescription>Primary role identified from the job description</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="prose max-w-none">
                    <h4 className="font-semibold mb-2">Key Responsibilities</h4>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      {jdAnalysis.responsibilities.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      Required Skills
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysis.required_skills.map((skill) => (
                        <Badge key={skill} variant="default">{skill}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5" />
                      Preferred Skills
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysis.preferred_skills.map((skill) => (
                        <Badge key={skill} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="skills" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Technical Competencies
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {jdAnalysis.technical_competencies.map((comp: TechnicalCompetency) => (
                      <div key={comp.name} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold">{comp.name}</h4>
                            <p className="text-sm text-muted-foreground">{comp.description}</p>
                          </div>
                          <Badge variant={
                            comp.importance === "high" ? "destructive" :
                            comp.importance === "medium" ? "warning" : "secondary"
                          }>
                            {comp.importance}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Behavioral Competencies
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {jdAnalysis.behavioral_competencies.map((comp: BehavioralCompetency) => (
                      <div key={comp.name} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold">{comp.name}</h4>
                            <p className="text-sm text-muted-foreground">{comp.description}</p>
                          </div>
                          <Badge variant={
                            comp.importance === "high" ? "destructive" :
                            comp.importance === "medium" ? "warning" : "secondary"
                          }>
                            {comp.importance}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="details" className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Experience Expectations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{jdAnalysis.experience_expectations || "Not specified"}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Qualifications</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      {jdAnalysis.qualifications.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Key Keywords</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {jdAnalysis.keywords.map((kw) => (
                      <Badge key={kw} variant="outline">{kw}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Key Concepts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {jdAnalysis.concepts.map((c) => (
                      <Badge key={c} variant="secondary">{c}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="raw" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Raw Analysis Data</CardTitle>
                  <CardDescription>Complete JSON response from the AI model</CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded overflow-x-auto text-sm max-h-96">
                    {JSON.stringify(jdAnalysis, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}

        {session.status === "completed" && (
          <Card className="mt-8 border-2 border-indigo-500/20 bg-gradient-to-r from-indigo-500/5 to-purple-500/5">
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-2">
                <div>
                  <h3 className="text-xl font-bold">Ready for your Mock Interview?</h3>
                  <p className="text-muted-foreground text-sm mt-1">
                    AI has analyzed your resume against the job description. Start your personalized Level 1 Screening Interview now.
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Link href={`/session/${sessionId}/job-fit`}>
                    <Button variant="outline">
                      View Job Fit Score
                    </Button>
                  </Link>
                  <Link href={`/session/${sessionId}/interview`}>
                    <Button size="lg" className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-semibold shadow-lg">
                      <Brain className="mr-2 h-5 w-5" />
                      Start AI Interview
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {session.status !== "completed" && (
          <Card className="border-primary/50">
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Brain className="mx-auto h-12 w-12 text-primary mb-4" />
                <h3 className="text-lg font-semibold mb-2">Ready to Analyze</h3>
                <p className="text-muted-foreground mb-6">
                  Click "Run Analysis" to have AI analyze the job description and extract key information.
                </p>
                <Button onClick={runAnalysis} disabled={analyzing} size="lg">
                  {analyzing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Brain className="mr-2 h-4 w-4" />
                      Run Analysis
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}