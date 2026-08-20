import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600 bg-green-100"
  if (score >= 60) return "text-yellow-600 bg-yellow-100"
  if (score >= 40) return "text-orange-600 bg-orange-100"
  return "text-red-600 bg-red-100"
}

export function getReadinessColor(level: string): string {
  switch (level) {
    case "strong_candidate":
      return "text-green-600 bg-green-100"
    case "interview_ready":
      return "text-blue-600 bg-blue-100"
    case "needs_preparation":
      return "text-yellow-600 bg-yellow-100"
    case "not_ready":
      return "text-red-600 bg-red-100"
    default:
      return "text-gray-600 bg-gray-100"
  }
}

export function getReadinessLabel(level: string): string {
  switch (level) {
    case "strong_candidate":
      return "🟢 Strong Candidate"
    case "interview_ready":
      return "🟡 Interview Ready"
    case "needs_preparation":
      return "🟠 Needs Preparation"
    case "not_ready":
      return "🔴 Not Ready"
    default:
      return "Unknown"
  }
}