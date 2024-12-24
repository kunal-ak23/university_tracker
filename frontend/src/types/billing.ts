import { Batch } from "./batch"

export interface BatchSnapshot {
  // We'll expand this later as needed
  id: string
  batch_id: string
  // Add other snapshot fields as needed
}

export interface Billing {
  id: string
  name: string
  batches: string[] | Batch[]  // Can be either IDs or full batch objects
  batch_snapshots: BatchSnapshot[]
  notes?: string
  total_amount: string
  total_payments: string
  balance_due: string
  total_oem_transfer_amount: string
  created_at: string
  updated_at: string
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