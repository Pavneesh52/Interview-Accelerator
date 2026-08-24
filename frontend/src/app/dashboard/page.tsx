"use client"

import { useSession, signOut } from "next-auth/react"
import Link from "next/link"
import { useState, useEffect } from "react"
import { LogOut, Plus, FileText, Search, Settings, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu"
import { formatDate } from "@/lib/utils"
import { api } from "@/lib/api"
import { AnalysisSession } from "@/lib/types"

export default function Dashboard() {
  const { data: session, status } = useSession()
  const [sessions, setSessions] = useState<AnalysisSession[]>([])
  const [loading, setLoading] = useState(true)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const fetchSessions = async () => {
    try {
      const response = await api.get("/analysis/sessions")
      setSessions(response.data)
    } catch (error) {
      console.error("Failed to fetch sessions:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (status === "authenticated") {
      fetchSessions()
    }
  }, [status])

  const handleSignOut = () => {
    signOut({ callbackUrl: "/" })
  }

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (status === "unauthenticated") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Please sign in to continue</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="text-xl font-bold">
            Interview Agent
          </Link>
          
          <div className="flex items-center gap-4">
            <Link href="/session/new" className="hidden sm:block">
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                New Session
              </Button>
            </Link>
            
            <DropdownMenu open={userMenuOpen} onOpenChange={setUserMenuOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src={session?.user?.image || ""} alt={session?.user?.name || ""} />
                    <AvatarFallback>
                      {session?.user?.name?.[0] || session?.user?.email?.[0]?.toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-2 py-1">
                  <p className="text-sm font-medium">{session?.user?.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{session?.user?.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/settings" className="flex w-full items-center px-2 py-1.5 text-sm">
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut} className="text-red-600 focus:text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">Manage your interview preparation sessions</p>
          </div>
          <Link href="/session/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Session
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="h-40" />
              </Card>
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-16">
            <Card className="max-w-md mx-auto">
              <CardContent className="py-12">
                <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-semibold">No sessions yet</h3>
                <p className="mt-2 text-muted-foreground">
                  Create your first interview preparation session by uploading a job description and resume.
                </p>
                <Link href="/session/new" className="mt-6 inline-block">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Session
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <Card key={session.id} className="transition-shadow hover:shadow-lg">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{session.job_fit?.rating || "Analysis Pending"}</CardTitle>
                      <p className="text-sm text-muted-foreground">{formatDate(session.created_at)}</p>
                    </div>
                    {session.job_fit && (
                      <Badge variant={
                        session.job_fit.score >= 80 ? "success" :
                        session.job_fit.score >= 60 ? "default" :
                        session.job_fit.score >= 40 ? "warning" : "destructive"
                      }>
                        {session.job_fit.score}%
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {session.jd_analysis && (
                    <div>
                      <p className="font-medium">{session.jd_analysis.role_title}</p>
                      <p className="text-sm text-muted-foreground truncate">{session.jd_analysis.responsibilities[0]}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Status: </span>
                    <Badge variant={
                      session.status === "completed" ? "success" :
                      session.status === "processing" ? "info" : "secondary"
                    } className="text-xs">
                      {session.status}
                    </Badge>
                  </div>
                  <div className="flex gap-2 pt-2">
                    {session.status === "completed" && (
                      <Link href={`/session/${session.id}/interview`}>
                        <Button variant="outline" className="flex-1" size="sm">
                          Start Interview
                        </Button>
                      </Link>
                    )}
                    {session.job_fit && (
                      <Link href={`/session/${session.id}/results`}>
                        <Button variant="default" className="flex-1" size="sm">
                          View Results
                        </Button>
                      </Link>
                    )}
                    {session.status !== "completed" && (
                      <Button variant="outline" className="flex-1" size="sm" disabled>
                        Analyzing...
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}