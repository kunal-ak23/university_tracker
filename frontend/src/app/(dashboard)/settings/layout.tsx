"use client"

import { Metadata } from "next"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/service/utils"

interface SettingsLayoutProps {
  children: React.ReactNode
}

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  return (
    <div className="space-y-6 p-6 pb-16">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">
          Manage your account settings and preferences.
        </p>
      </div>
      <Separator className="my-6" />
      <div className="flex flex-col space-y-8">
        <nav className="flex space-x-2 border-b">
          <Link
            href="/settings/users"
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors hover:text-primary",
              "data-[current=true]:border-b-2 data-[current=true]:border-primary",
            )}
            data-current={usePathname()?.startsWith('/settings/users')}
          >
            Users
          </Link>
          <Link
            href="/settings/profile"
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors hover:text-primary",
              "data-[current=true]:border-b-2 data-[current=true]:border-primary",
            )}
            data-current={usePathname()?.startsWith('/settings/profile')}
          >
            Profile
          </Link>
        </nav>
        <div className="flex-1">{children}</div>
      </div>
    </div>
  )
} 