"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { formatCurrency } from "@/service/utils"
import { getRecentPayments } from "@/service/api/dashboard"
import type { RecentPayment } from "@/service/api/dashboard"

export function RecentPayments() {
  const [payments, setPayments] = useState<RecentPayment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadPayments = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await getRecentPayments()
        setPayments(response.results)
        console.log(response.results);
      } catch (error) {
        console.error('Failed to load recent payments:', error)
        setError('Failed to load recent payments')
      } finally {
        setIsLoading(false)
      }
    }

    loadPayments()
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-muted-foreground">Loading payments...</div>
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

  if (!payments.length) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <div className="text-muted-foreground">No recent payments</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {payments.map((payment) => (
        <div key={payment.id} className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium leading-none">{payment.name}</p>
            <div className="flex items-center gap-2">
              <p className="text-sm text-muted-foreground">
                {new Date(payment.payment_date).toLocaleDateString()}
              </p>
              <Badge variant="outline">
                {payment?.payment_method?.replace('_', ' ')}
              </Badge>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div className="font-medium">{formatCurrency(payment.amount)}</div>
            <Badge variant={
              payment.status === "completed"
                ? "default"
                : payment.status === "failed"
                ? "destructive"
                : "secondary"
            }>
              {payment.status}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  )
} 