import { OEM } from "./oem"

export interface Program {
  id: number
  provider: OEM
  created_at: string
  updated_at: string
  version: number
  name: string
  program_code: string
  duration: number
  duration_unit: string
  description: string
  prerequisites: string
}

export interface ProgramFormData {
  name: string
  program_code: string
  duration: number
  duration_unit: string
  description?: string
  prerequisites?: string
  provider_id: number
}

export type DurationUnit = "Years" | "Months" | "Weeks" | "Days" 