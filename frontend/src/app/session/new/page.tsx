"use client"

import * as React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { FileText, Upload, Loader2, CheckCircle, AlertCircle, Trash2, Edit2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"
import { JobDescription, Resume } from "@/lib/types"
import { toast } from "@/components/ui/use-toast"

interface UploadedFile {
  id: string
  file: File
  content: string
  name: string
}

export default function NewSessionPage() {
  const router = useRouter()
  const [jdFile, setJdFile] = useState<UploadedFile | null>(null)
  const [jdText, setJdText] = useState("")
  const [jdMode, setJdMode] = useState<"upload" | "paste">("upload")
  const [jdTitle, setJdTitle] = useState("")
  
  const [resumeFile, setResumeFile] = useState<UploadedFile | null>(null)
  const [resumeText, setResumeText] = useState("")
  const [resumeMode, setResumeMode] = useState<"upload" | "paste">("upload")
  
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<"jd" | "resume" | "review">("jd")
  const [jdDocId, setJdDocId] = useState<string | null>(null)
  const [resumeDocId, setResumeDocId] = useState<string | null>(null)

  const handleJDFileUpload = async (file: File) => {
    if (!file.type.match(/pdf|word|text/)) {
      toast({ title: "Invalid file type", description: "Please upload PDF, DOCX, or TXT file", variant: "destructive" })
      return
    }
    
    const content = await file.text()
    setJdFile({ id: "jd", file, content, name: file.name })
    setJdTitle(file.name.replace(/\.[^/.]+$/, ""))
  }

  const handleResumeFileUpload = async (file: File) => {
    if (!file.type.match(/pdf|word|text/)) {
      toast({ title: "Invalid file type", description: "Please upload PDF, DOCX, or TXT file", variant: "destructive" })
      return
    }
    
    const content = await file.text()
    setResumeFile({ id: "resume", file, content, name: file.name })
  }

  const handleJDSubmit = async () => {
    if (!jdFile && !jdText.trim()) {
      toast({ title: "Missing JD", description: "Please upload or paste a job description", variant: "destructive" })
      return
    }
    
    setLoading(true)
    try {
      if (jdFile) {
        const formData = new FormData()
        formData.append("file", jdFile.file)
        const response = await api.post("/documents/jd/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" }
        })
        console.log("JD upload response:", response.data)
        setJdDocId(response.data.document_id)
      } else {
        const response = await api.post("/documents/jd/paste", {
          title: jdTitle || "Pasted Job Description",
          raw_text: jdText
        })
        console.log("JD paste response:", response.data)
        setJdDocId(response.data.id)
      }
      
      setStep("resume")
      toast({ title: "JD saved", description: "Now add your resume" })
    } catch (error) {
      toast({ title: "Error", description: "Failed to save job description", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const handleResumeSubmit = async () => {
    if (!resumeFile && !resumeText.trim()) {
      toast({ title: "Missing Resume", description: "Please upload or paste your resume", variant: "destructive" })
      return
    }
    
    setLoading(true)
    try {
      if (resumeFile) {
        const formData = new FormData()
        formData.append("file", resumeFile.file)
        const response = await api.post("/documents/resume/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" }
        })
        console.log("Resume upload response:", response.data)
        setResumeDocId(response.data.document_id)
      } else {
        const response = await api.post("/documents/resume/paste", {
          raw_text: resumeText
        })
        console.log("Resume paste response:", response.data)
        setResumeDocId(response.data.id)
      }
      
      setStep("review")
      toast({ title: "Resume saved", description: "Review and create session" })
    } catch (error) {
      toast({ title: "Error", description: "Failed to save resume", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSession = async () => {
    setLoading(true)
    try {
      console.log("Creating session with jdDocId:", jdDocId, "resumeDocId:", resumeDocId)
      if (!jdDocId || !resumeDocId) {
        toast({ title: "Error", description: "Please complete JD and Resume steps first", variant: "destructive" })
        setLoading(false)
        return
      }
      const response = await api.post("/analysis/sessions", {
        jd_id: jdDocId,
        resume_id: resumeDocId
      })
      
      // We need to get the actual IDs from the created documents
      // For now, we'll navigate to the session page
      toast({ title: "Session created", description: "Starting analysis..." })
      router.push(`/session/${response.data.id}`)
    } catch (error) {
      toast({ title: "Error", description: "Failed to create session", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const handleJdModeChange = (value: string) => {
    setJdMode(value as "upload" | "paste")
  }

  const handleResumeModeChange = (value: string) => {
    setResumeMode(value as "upload" | "paste")
  }

  const renderJDStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Job Description</h3>
        <Tabs defaultValue={jdMode} onValueChange={handleJdModeChange}>
          <TabsList className="w-full">
            <TabsTrigger value="upload" className="flex-1">Upload File</TabsTrigger>
            <TabsTrigger value="paste" className="flex-1">Paste Text</TabsTrigger>
          </TabsList>
          <TabsContent value="upload" className="mt-4">
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                jdFile ? "border-green-500 bg-green-50" : "border-muted-foreground/25 hover:border-primary/50"
              }`}
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("border-primary") }}
              onDragLeave={(e) => { e.currentTarget.classList.remove("border-primary") }}
              onDrop={(e) => {
                e.preventDefault()
                e.currentTarget.classList.remove("border-primary")
                if (e.dataTransfer.files[0]) handleJDFileUpload(e.dataTransfer.files[0])
              }}
            >
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => e.target.files?.[0] && handleJDFileUpload(e.target.files[0])}
                className="hidden"
                id="jd-file"
              />
              <label htmlFor="jd-file" className="cursor-pointer">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">Drag & drop or click to upload</p>
                <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, or TXT (max 10MB)</p>
              </label>
              
              {jdFile && (
                <div className="mt-4 p-4 bg-white border rounded-lg text-left">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary" />
                      <div>
                        <p className="font-medium">{jdFile.name}</p>
                        <p className="text-sm text-muted-foreground">{(jdFile.content.length / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setJdFile(null)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <Input
                    value={jdTitle}
                    onChange={(e) => setJdTitle(e.target.value)}
                    placeholder="Job Title"
                    className="mt-3"
                  />
                </div>
              )}
            </div>
          </TabsContent>
          <TabsContent value="paste" className="mt-4">
            <Textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the job description here..."
              className="min-h-[200px] font-mono text-sm"
              rows={10}
            />
            <Input
              value={jdTitle}
              onChange={(e) => setJdTitle(e.target.value)}
              placeholder="Job Title (optional)"
              className="mt-3"
            />
          </TabsContent>
        </Tabs>
      </div>
      
      <Button onClick={handleJDSubmit} disabled={loading} className="w-full" size="lg">
        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <>Continue to Resume <CheckCircle className="ml-2 h-4 w-4" /></>}
      </Button>
    </div>
  )

  const renderResumeStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Your Resume</h3>
        <Tabs defaultValue={resumeMode} onValueChange={handleResumeModeChange}>
          <TabsList className="w-full">
            <TabsTrigger value="upload" className="flex-1">Upload File</TabsTrigger>
            <TabsTrigger value="paste" className="flex-1">Paste Text</TabsTrigger>
          </TabsList>
          <TabsContent value="upload" className="mt-4">
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                resumeFile ? "border-green-500 bg-green-50" : "border-muted-foreground/25 hover:border-primary/50"
              }`}
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("border-primary") }}
              onDragLeave={(e) => { e.currentTarget.classList.remove("border-primary") }}
              onDrop={(e) => {
                e.preventDefault()
                e.currentTarget.classList.remove("border-primary")
                if (e.dataTransfer.files[0]) handleResumeFileUpload(e.dataTransfer.files[0])
              }}
            >
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => e.target.files?.[0] && handleResumeFileUpload(e.target.files[0])}
                className="hidden"
                id="resume-file"
              />
              <label htmlFor="resume-file" className="cursor-pointer">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">Drag & drop or click to upload</p>
                <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, or TXT (max 10MB)</p>
              </label>
              
              {resumeFile && (
                <div className="mt-4 p-4 bg-white border rounded-lg text-left">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary" />
                      <div>
                        <p className="font-medium">{resumeFile.name}</p>
                        <p className="text-sm text-muted-foreground">{(resumeFile.content.length / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setResumeFile(null)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
          <TabsContent value="paste" className="mt-4">
            <Textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume here..."
              className="min-h-[200px] font-mono text-sm"
              rows={10}
            />
          </TabsContent>
        </Tabs>
      </div>
      
      <div className="flex gap-4">
        <Button variant="outline" onClick={() => setStep("jd")} className="flex-1">
          Back
        </Button>
        <Button onClick={handleResumeSubmit} disabled={loading} className="flex-1" size="lg">
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <>Continue to Review <CheckCircle className="ml-2 h-4 w-4" /></>}
        </Button>
      </div>
    </div>
  )

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Review & Create Session</h3>
        <Card>
          <CardHeader>
            <CardTitle>Job Description</CardTitle>
            <CardDescription>{jdFile?.name || "Pasted text"}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{jdText.substring(0, 200)}...</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Resume</CardTitle>
            <CardDescription>{resumeFile?.name || "Pasted text"}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{resumeText.substring(0, 200)}...</p>
          </CardContent>
        </Card>
      </div>
      
      <div className="flex gap-4">
        <Button variant="outline" onClick={() => setStep("resume")} className="flex-1">
          Back
        </Button>
        <Button onClick={handleCreateSession} disabled={loading} className="flex-1" size="lg">
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <>Create Session & Analyze <CheckCircle className="ml-2 h-4 w-4" /></>}
        </Button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <a href="/dashboard" className="text-xl font-bold">Interview Agent</a>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Create New Session</h1>
          <p className="text-muted-foreground">Upload a job description and your resume to get started</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center mb-8">
          {["jd", "resume", "review"].map((s, i) => (
            <React.Fragment key={s}>
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step === s || (["jd", "resume", "review"].indexOf(step) > i)
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}>
                  {step === s || (["jd", "resume", "review"].indexOf(step) > i) ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    i + 1
                  )}
                </div>
                {i < 2 && <div className={`w-20 h-1 mx-2 ${step === "review" || (step !== "jd" && i === 0) ? "bg-primary" : "bg-muted"}`} />}
              </div>
              <span className={`text-xs text-center w-24 mt-1 ${step === s ? "font-medium text-foreground" : "text-muted-foreground"}`}>
                {s === "jd" ? "Job Description" : s === "resume" ? "Resume" : "Review"}
              </span>
            </React.Fragment>
          ))}
        </div>

        <Card>
          <CardContent className="p-6">
            {step === "jd" && renderJDStep()}
            {step === "resume" && renderResumeStep()}
            {step === "review" && renderReviewStep()}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}