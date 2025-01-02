import { Batch } from "./batch"

export interface BatchSnapshot {
  // We'll expand this later as needed
  id: number
  batch: number
  batch_name: string
  batch_stream: string
  batch_contract: string
  number_of_students: number
  cost_per_student: string
  tax_rate: string
  oem_transfer_price: string
  status: string
  created_at: string
  updated_at: string
}

export interface Billing {
  id: string
  name: string
  batches: number[] | Batch[]  // Can be either IDs or full batch objects
  batch_snapshots: BatchSnapshot[]
  notes?: string
  total_amount: string
  total_payments: string
  balance_due: string
  total_oem_transfer_amount: string
  status: 'draft' | 'active' | 'archived'
  created_at: string
  updated_at: string
  days_overdue: number
  due_date: string
  dueDate: Date
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  invoice_status: string
  invoice_id: string
}

export interface BillingCreateInput {
  name: string
  batches: string[]  // Batch IDs
  notes?: string
}

export interface BillingResponse {
  count: number
  next: string | null
  previous: string | null
  results: Billing[]
} 
