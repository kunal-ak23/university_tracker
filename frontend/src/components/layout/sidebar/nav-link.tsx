"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/service/utils"
import { HTMLAttributes } from "react"

interface NavLinkProps extends HTMLAttributes<HTMLAnchorElement> {
  href: string
  children: React.ReactNode
}

export function NavLink({ href, children, className, ...props }: NavLinkProps) {
  const pathname = usePathname()
  const isActive = pathname === href

  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground",
        isActive ? "bg-accent" : "transparent",
        className
      )}
      {...props}
    >
      {children}
    </Link>
  )
} 
