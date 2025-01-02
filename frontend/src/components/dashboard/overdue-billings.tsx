"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { formatCurrency } from "@/service/utils"
import { AlertCircle } from "lucide-react"
import { getOverdueBillings } from "@/service/api/dashboard"
import type { Billing } from "@/types/billing"

export function OverdueBillings() {
  const [billings, setBillings] = useState<Billing[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)



  useEffect(() => {
    const loadBillings = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = (await getOverdueBillings()).results
        setBillings(response)
      } catch (error) {
        console.error('Failed to load overdue billings:', error)
        setError('Failed to load overdue billings')
      } finally {
        setIsLoading(false)
      }
    }

    loadBillings()
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-muted-foreground">Loading overdue billings...</div>
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

  if (!billings.length) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-muted-foreground">No overdue billings</div>
      </div>
    )
  }


  billings.map((billing) => {
    const dueDate =  new Date();
    dueDate.setDate(dueDate.getDate() - billing.days_overdue);
    billing.dueDate = dueDate;
  })


  return (
    <div className="space-y-8">
      {billings.map((billing) => (
        <div key={billing.id} className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium leading-none">{billing.name}</p>
            <div className="flex items-center gap-2">
              <p className="text-sm text-muted-foreground">
                Due Date: {billing.dueDate.toLocaleDateString()}
              </p>
              <Badge variant="destructive" className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {billing.days_overdue} days overdue
              </Badge>
            </div>
          </div>
          <div className="font-medium text-red-500">
            {formatCurrency(parseFloat(billing.balance_due))}
          </div>
        </div>
      ))}
    </div>
  )
} 