import { University } from "./university"

export interface Stream {
  id: string
  name: string
  duration: number
  duration_unit: 'Days' | 'Months' | 'Years'
  university: University
  description: string | null
  created_at: string
  updated_at: string
} 