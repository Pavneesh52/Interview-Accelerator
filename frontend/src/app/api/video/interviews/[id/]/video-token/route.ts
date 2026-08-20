import { NextRequest, NextResponse } from "next/server"
import { api } from "@/lib/api"

export async function POST(
  request: NextRequest,
  context: { params: Promise<Record<string, string>> }
) {
  try {
    const { id } = await context.params
    const response = await api.post(`/video/interviews/${id}/video-token`)
    return NextResponse.json(response.data)
  } catch (error: any) {
    return NextResponse.json(
      { error: error.response?.data?.detail || "Failed to get video token" },
      { status: error.response?.status || 500 }
    )
  }
}