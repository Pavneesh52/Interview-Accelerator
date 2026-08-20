import { NextRequest, NextResponse } from "next/server"
import { api } from "@/lib/api"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email, password, name } = body
    
    const response = await api.post("/auth/register", {
      email,
      password,
      full_name: name,
    })
    
    return NextResponse.json(response.data)
  } catch (error: any) {
    return NextResponse.json(
      { error: error.response?.data?.detail || "Registration failed" },
      { status: error.response?.status || 500 }
    )
  }
}