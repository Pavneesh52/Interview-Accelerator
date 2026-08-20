"use client"

import { SessionProvider } from "next-auth/react"
import { ToastProvider, ToastViewport } from "@/components/ui/toast"
import { ReactNode } from "react"

export function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      {children}
      <ToastProvider>
        <ToastViewport />
      </ToastProvider>
    </SessionProvider>
  )
}