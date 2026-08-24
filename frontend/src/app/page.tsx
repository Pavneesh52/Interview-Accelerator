import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"

export default async function Home() {
  let session = null
  try {
    session = await getServerSession(authOptions)
  } catch (error) {
    console.error("Home page SSR session check error:", error)
  }
  
  if (session) {
    redirect("/dashboard")
  } else {
    redirect("/login")
  }
}