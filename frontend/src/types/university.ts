export interface University {
  id: string
  name: string
  website: string
  established_year: number
  accreditation: string | null
  contact_email: string | null
  contact_phone: string | null
  address: string | null
  created_at: string
  updated_at: string
}

export interface UniversityFormData {
  name: string
  website: string
  established_year: number
  accreditation?: string
  contact_email?: string
  contact_phone?: string
  address?: string
  poc_id?: string
} 