import { OEM } from "./oem"

export interface Program {
  id: string
  name: string
  program_code: string
  provider: OEM
  duration: number
  duration_unit: 'Days' | 'Months' | 'Years'
  description: string | null
  prerequisites: string | null
  created_at: string
  updated_at: string
} 