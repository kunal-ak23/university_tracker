import type { Metadata } from "next"
import { Inter, Righteous } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/shared/theme-provider"
import { auth } from "@/auth"
import { SessionProvider } from "next-auth/react"
import { Toaster } from "@/components/ui/toaster"
import { cn } from '@/service/utils'

const inter = Inter({ subsets: ["latin"] })
const righteous = Righteous({ weight: '400', subsets: ['latin'] })

export const metadata: Metadata = {
  title: "Trackie",
  description: "University Batch Tracking System",
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(inter.className, "min-h-screen")}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <SessionProvider session={session}>
            {children}
            <Toaster />
          </SessionProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
