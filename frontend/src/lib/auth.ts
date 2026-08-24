import NextAuth, { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { api } from "./api"

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",

      credentials: {
        email: {
          label: "Email",
          type: "email",
        },
        password: {
          label: "Password",
          type: "password",
        },
      },

      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          console.log("Missing email or password")
          return null
        }

        try {
          console.log("Attempting login:", credentials.email)

          const response = await api.post("/auth/login", {
            email: credentials.email,
            password: credentials.password,
          })

          console.log("Backend login status:", response.status)
          console.log("Backend login response:", response.data)

          const {
            access_token,
            expires_in,
            user,
          } = response.data

          if (!access_token) {
            console.error("No access_token returned from backend")
            return null
          }

          return {
            id: user?.id?.toString() || "1",
            email: user?.email || credentials.email,
            name: user?.name || null,
            image: user?.image || null,
            accessToken: access_token,
            expiresIn: expires_in,
          }
        } catch (error: any) {
          console.error("========== LOGIN ERROR ==========")

          if (error.response) {
            console.error("Status:", error.response.status)
            console.error("Data:", error.response.data)
          } else {
            console.error("Message:", error.message)
          }

          console.error("=================================")

          return null
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken
        token.expiresIn = user.expiresIn
        token.id = user.id
      }

      return token
    },

    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string
      }

      session.accessToken = token.accessToken
      session.expiresIn = token.expiresIn

      return session
    },
  },

  pages: {
    signIn: "/login",
  },

  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60,
  },

  secret: process.env.NEXTAUTH_SECRET || "interview-accelerator-default-secret-key-2026",
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }