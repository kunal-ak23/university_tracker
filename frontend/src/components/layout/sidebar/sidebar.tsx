"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { sidebarConfig } from "@/config/sidebar"
import { ChevronLeft, ChevronRight, ChevronDown } from "lucide-react"
import { cn } from "@/service/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

const SIDEBAR_STATE_KEY = 'sidebar-collapsed'

export function Sidebar({className}: {className?: string}) {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Load initial state from localStorage
  useEffect(() => {
    const storedState = localStorage.getItem(SIDEBAR_STATE_KEY)
    if (storedState !== null) {
      setIsCollapsed(storedState === 'true')
    }
  }, [])

  // Update localStorage when state changes
  const toggleCollapsed = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    localStorage.setItem(SIDEBAR_STATE_KEY, newState.toString())
  }

  return (
    <div className={cn(
      "relative flex flex-col bg-background",
      isCollapsed ? "w-16" : "w-64",
      "transition-all duration-300 ease-in-out",
      className
    )}>
      <div className="hidden lg:block">
        <Button
          variant="ghost"
          size="icon"
          className="absolute -right-4 top-6 h-8 w-8 rounded-full border bg-background"
          onClick={toggleCollapsed}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <div className="space-y-4 py-4">
        <div className="px-3 py-2">
          <div className="space-y-1">
            <TooltipProvider delayDuration={0}>
              {sidebarConfig.map((item, index) => {
                if (item.items) {
                  // Group item
                  return (
                    <Collapsible key={index}>
                      <CollapsibleTrigger asChild>
                        <Button
                          variant="ghost"
                          className={cn(
                            "w-full justify-start",
                            isCollapsed && "justify-center px-2"
                          )}
                        >
                          <item.icon className={cn(
                            "h-4 w-4",
                            !isCollapsed && "mr-2"
                          )} />
                          {!isCollapsed && (
                            <>
                              {item.title}
                              <ChevronDown className="ml-auto h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        {item.items.map((subItem) => (
                          <Tooltip key={subItem.href} delayDuration={0}>
                            <TooltipTrigger asChild>
                              <Link href={subItem.href}>
                                <Button
                                  variant={pathname === subItem.href ? "secondary" : "ghost"}
                                  className={cn(
                                    "w-full justify-start pl-8",
                                    isCollapsed && "justify-center px-2"
                                  )}
                                >
                                  <subItem.icon className={cn(
                                    "h-4 w-4",
                                    !isCollapsed && "mr-2"
                                  )} />
                                  {!isCollapsed && subItem.title}
                                </Button>
                              </Link>
                            </TooltipTrigger>
                            {isCollapsed && (
                              <TooltipContent side="right">
                                {subItem.title}
                              </TooltipContent>
                            )}
                          </Tooltip>
                        ))}
                      </CollapsibleContent>
                    </Collapsible>
                  )
                }

                // Single item
                return (
                  <Tooltip key={item.href} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <Link href={item.href}>
                        <Button
                          variant={pathname === item.href ? "secondary" : "ghost"}
                          className={cn(
                            "w-full justify-start",
                            isCollapsed && "justify-center px-2"
                          )}
                        >
                          <item.icon className={cn(
                            "h-4 w-4",
                            !isCollapsed && "mr-2"
                          )} />
                          {!isCollapsed && item.title}
                        </Button>
                      </Link>
                    </TooltipTrigger>
                    {isCollapsed && (
                      <TooltipContent side="right">
                        {item.title}
                      </TooltipContent>
                    )}
                  </Tooltip>
                )
              })}
            </TooltipProvider>
          </div>
        </div>
      </div>
    </div>
  )
} 
