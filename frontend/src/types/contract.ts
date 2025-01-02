import {z} from "zod";
import { Program } from "./program";
export interface ContractProgram {
  id: number
  program: Program
}

export interface ContractFile {
  id: number
  contract: number
  file_type: string
  file: string
  description: string
  uploaded_by: number
}

export interface Stream {
  id: number
  name: string
  duration: number
  duration_unit: string
  description: string
}

export interface OEM {
  id: number
  name: string
  website: string
  contact_email: string
  contact_phone: string
  address: string
}

export interface University {
  id: number
  name: string
  website: string
  established_year: number
  accreditation: string
  contact_email: string
  contact_phone: string
  address: string
}

export interface Contract {
  id: string
  name: string
  cost_per_student: string
  oem_transfer_price: string
  start_date: string | null
  end_date: string | null
  status: string 
  notes: string | null
  tax_rate: number
  contract_programs: ContractProgram[]
  contract_files: ContractFile[]
  streams: Stream[]
  oem: OEM | null
  university: University | null
  programs: Program[]
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
