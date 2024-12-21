import { z } from "zod"

export interface Provider {
  id: number
  created_at: string
  updated_at: string
  version: number
  name: string
  website: string
  contact_email: string | null
  contact_phone: string | null
  address: string
  poc: number
}

export interface Program {
  id: number
  provider: Provider
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

export interface ContractProgram {
  id: number
  program: Program
  created_at: string
  updated_at: string
  version: number
  contract: number
}

export interface Stream {
  id: number
  created_at: string
  updated_at: string
  version: number
  name: string
  duration: number
  duration_unit: string
  description: string
  university: number
}

export interface University {
  id: number
  created_at: string
  updated_at: string
  version: number
  name: string
  description: string
}

export interface Contract {
  id: number
  contract_programs: ContractProgram[]
  streams: Stream[]
  oem: Provider
  programs: Program[]
  created_at: string
  updated_at: string
  version: number
  name: string
  cost_per_student: string
  oem_transfer_price: string
  start_date: string
  end_date: string
  status: 'active' | 'pending' | 'expired'
  notes: string
  tax_rate: number
  university: University
  contract_files: ContractFile[]
}

export interface ContractFile {
  id: number
  created_at: string
  updated_at: string
  version: number
  file_type: string
  file: string
  description: string
  contract: number
  uploaded_by: number
}

export const contractFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  cost_per_student: z.string().min(1, "Cost per student is required"),
  oem_transfer_price: z.string().min(1, "OEM transfer price is required"),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().min(1, "End date is required"),
  notes: z.string().optional(),
  status: z.enum(["active", "pending", "expired"]),
  tax_rate: z.number(),
  oem_id: z.number(),
  university_id: z.number(),
  streams_ids: z.array(z.number()).refine(
    (streams) => streams.length > 0,
    { message: "Please select at least one stream" }
  ),
  programs_ids: z.array(z.number()).refine(
    (programs) => programs.length > 0,
    { message: "Please select at least one program" }
  )
})

export type ContractFormData = z.infer<typeof contractFormSchema> 