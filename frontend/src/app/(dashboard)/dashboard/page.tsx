"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { IndianRupee, Users, FileText, AlertCircle } from "lucide-react"
import { Overview } from "@/components/dashboard/overview"
import { RecentInvoices } from "@/components/dashboard/recent-invoices"
import { RecentPayments } from "@/components/dashboard/recent-payments"
import { OverdueBillings } from "@/components/dashboard/overdue-billings"
import { getDashboardSummary } from "@/service/api/dashboard"
import type { DashboardSummary } from "@/service/api/dashboard"
import { formatCurrency } from "@/service/utils"


export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSummary = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await getDashboardSummary()
        console.log(data);
        setSummary(data)
      } catch (error) {
        console.error('Failed to load dashboard summary:', error)
        setError('Failed to load dashboard data. Please try again later.')
      } finally {
        setIsLoading(false)
      }
    }

    loadSummary()
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-muted-foreground">Loading dashboard data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-destructive">{error}</div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-muted-foreground">No dashboard data available</div>
      </div>
    )
  }

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>
      
      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <IndianRupee className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.total_revenue.current)}</div>
            <p className="text-xs text-muted-foreground">
              {summary.total_revenue.percentage_change >= 0 ? '+' : ''}
              {summary.total_revenue.percentage_change.toFixed(1)}% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Batches</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.active_batches.current}</div>
            <p className="text-xs text-muted-foreground">
              +{summary.active_batches.new_this_month} new this month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Invoices</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.pending_invoices.count}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(summary.pending_invoices.total_value)} total value
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue Payments</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.overdue_payments.count}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(summary.overdue_payments.total_value)} overdue
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Revenue Overview</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <Overview />
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Invoices</CardTitle>
          </CardHeader>
          <CardContent>
            <RecentInvoices />
          </CardContent>
        </Card>
      </div>

      {/* Additional Information */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Payments</CardTitle>
          </CardHeader>
          <CardContent>
            <RecentPayments />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Overdue Billings</CardTitle>
          </CardHeader>
          <CardContent>
            <OverdueBillings />
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 