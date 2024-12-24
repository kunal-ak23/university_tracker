"use client"

import { UserNav } from "@/components/layout/header/user-nav"
import { ModeToggle } from "@/components/shared/mode-toggle"
import Image from "next/image"
import { useTheme } from "next-themes"
import { Righteous } from "next/font/google"
import { cn } from "@/service/utils"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"

const righteous = Righteous({ weight: '400', subsets: ['latin'] })

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme } = useTheme()

  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4">
        {/* Mobile menu button - only show on mobile */}
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onMenuClick}
        >
          <Menu className="h-6 w-6" />
        </Button>

        {/* Logo and title - centered on mobile, left-aligned on desktop */}
        <div className="flex items-center flex-1 justify-center lg:justify-start">
          <Image
            src={theme === 'dark' ? '/images/dark_logo.png' : '/images/logo.png'}
            alt="Trackie Logo"
            width={50}
            height={50}
            className="min-w-[50px]"
          />
          <span className={cn(
            righteous.className,
            "ml-2 text-xl font-bold tracking-wide"
          )}>
            Trackie
          </span>
        </div>

        {/* Right side actions */}
        <div className="flex items-center space-x-4">
          <ModeToggle />
          <UserNav />
        </div>
      </div>
    </div>
  )
} 
