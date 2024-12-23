import { Contract } from "./contract"
import { Stream } from "./stream"

export interface Batch {
  id: string
  name: string
  stream: Stream | number
  contract: Contract | number
  number_of_students: number
  start_year: number
  end_year: number
  start_date: string
  end_date: string
  effective_cost_per_student: string
  cost_per_student_override: string | null
  oem_transfer_price: string
  oem_transfer_price_override: string | null
  tax_rate: number
  tax_rate_override: number | null
  effective_tax_rate: number
  status: 'ongoing' | 'completed' | 'planned'
  notes: string | null
  created_at: string
  updated_at: string
} 