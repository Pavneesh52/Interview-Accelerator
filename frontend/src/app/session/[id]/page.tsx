"use client"

import { useEffect } from "react"
import { useParams, useRouter } from "next/navigation"

export default function SessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  useEffect(() => {
    // Redirect to the analysis page for this session
    router.replace(`/session/${sessionId}/analysis`)
  }, [sessionId, router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  )
}
