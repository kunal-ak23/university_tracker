import { Contract } from "./contract"
import { Stream } from "./stream"

export interface Batch {
  id: number
  name: string
  status: string
  number_of_students: number
  start_year: number
  end_year: number
  batch_stream: string
  notes?: string
  cost_per_student: string
  oem_transfer_price: string
  tax_rate: string
  effective_cost_per_student: string
  effective_oem_transfer_price: string
  effective_tax_rate: string
} 