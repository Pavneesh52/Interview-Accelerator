"use client"

import { useParams, useRouter } from "next/navigation"
import { InterviewSimulator } from "@/components/InterviewSimulator"

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  return (
    <InterviewSimulator
      sessionId={sessionId}
      onExit={() => router.push("/dashboard")}
    />
  )
}