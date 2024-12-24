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
  contract_programs: Array<{
    id: number
    program: {
      id: number
      name: string
      program_code: string
      duration: number
      duration_unit: string
      description: string
      prerequisites: string
      provider: any
    }
  }>
  contract_files: Array<{
    id: number
    contract: number
    file_type: string
    file: string
    description: string
    uploaded_by: number
  }>
  streams: Array<{
    id: number
    name: string
    duration: number
    duration_unit: string
    description: string
  }>
  oem: {
    id: number
    name: string
    website: string
    contact_email: string
    contact_phone: string
    address: string
  } | null
  university: {
    id: number
    name: string
    website: string
    established_year: number
    accreditation: string
    contact_email: string
    contact_phone: string
    address: string
  } | null
  programs: Array<{
    id: number
    name: string
    program_code: string
    duration: number
    duration_unit: string
    description: string
    prerequisites: string
  }>
} 