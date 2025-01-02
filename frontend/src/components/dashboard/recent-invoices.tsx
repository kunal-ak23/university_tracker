"use client"

import { useEffect, useState } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { formatCurrency } from "@/service/utils"
import { getRecentInvoices } from "@/service/api/dashboard"
import type { RecentInvoice } from "@/service/api/dashboard"

export function RecentInvoices() {
  const [invoices, setInvoices] = useState<RecentInvoice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadInvoices = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await getRecentInvoices()
        setInvoices(response.results)
      } catch (error) {
        console.error('Failed to load recent invoices:', error)
        setError('Failed to load recent invoices')
      } finally {
        setIsLoading(false)
      }
    }

    loadInvoices()
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-muted-foreground">Loading invoices...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-destructive">{error}</div>
      </div>
    )
  }

  if (!invoices.length) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-muted-foreground">No recent invoices</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {invoices.map((invoice) => (
        <div key={invoice.id} className="flex items-center">
          <Avatar className="h-9 w-9">
            <AvatarFallback>
              {invoice.name.split(" ").map((n) => n[0]).join("")}
            </AvatarFallback>
          </Avatar>
          <div className="ml-4 space-y-1">
            <p className="text-sm font-medium leading-none">{invoice.name}</p>
            <p className="text-sm text-muted-foreground">
              {invoice.id}
            </p>
          </div>
          <div className="ml-auto font-medium">
            <div className={
              invoice.status === "paid"
                ? "text-green-500"
                : invoice.status === "overdue"
                ? "text-red-500"
                : "text-gray-500"
            }>
              {formatCurrency(invoice.amount)}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
} 