import { Billing } from "@/types/billing"
import { apiFetch } from "./fetch"

export interface DashboardSummary {
  total_revenue: {
    current: number
    previous: number
    percentage_change: number
  }
  active_batches: {
    current: number
    new_this_month: number
  }
  pending_invoices: {
    count: number
    total_value: number
  }
  overdue_payments: {
    count: number
    total_value: number
  }
}

export interface RevenueData {
  name: string
  total: number
}

export interface RecentInvoice {
  id: string
  name: string
  amount: number
  status: 'unpaid' | 'paid' | 'partially_paid' | 'overdue'
  created_at: string
}

export interface RecentPayment {
  id: string
  name: string
  amount: number
  method: 'cash' | 'bank_transfer' | 'cheque' | 'upi'
  status: 'completed' | 'pending' | 'failed'
  payment_date: string
  payment_method: 'cash' | 'bank_transfer' | 'cheque' | 'upi'
  date: string
}

export interface OverdueBilling {
  id: string
  name: string
  amount: number
  due_date: string
  days_overdue: number
}

export interface PaginatedResponse<T> {
  results: T[]
  total: number
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch('/dashboard/summary/')
}

export async function getRevenueOverview(year: number, month?: number): Promise<{ data: RevenueData[] }> {
  const searchParams = new URLSearchParams()
  searchParams.append('year', year.toString())
  if (month) searchParams.append('month', month.toString())
  
  return apiFetch(`/dashboard/revenue_overview/?${searchParams.toString()}`)
}

export async function getRecentInvoices(limit: number = 5, page: number = 1): Promise<PaginatedResponse<RecentInvoice>> {
  const searchParams = new URLSearchParams()
  searchParams.append('limit', limit.toString())
  searchParams.append('page', page.toString())
  
  return apiFetch(`/dashboard/recent_invoices/?${searchParams.toString()}`)
}

export async function getRecentPayments(limit: number = 5, page: number = 1): Promise<PaginatedResponse<RecentPayment>> {
  const searchParams = new URLSearchParams()
  searchParams.append('limit', limit.toString())
  searchParams.append('page', page.toString())
  
  return apiFetch(`/dashboard/recent_payments/?${searchParams.toString()}`)
}

export async function getOverdueBillings(limit: number = 5, page: number = 1): Promise<PaginatedResponse<Billing>> {
  const searchParams = new URLSearchParams()
  searchParams.append('limit', limit.toString())
  searchParams.append('page', page.toString())
  
  return apiFetch(`/dashboard/overdue_billings/?${searchParams.toString()}`)
} 