export interface University {
  id: string
  name: string
  website: string
  established_year: number | undefined
  accreditation?: string
  contact_email?: string
  contact_phone?: string
  address?: string
  location?: string
  poc?: {
    id: string
    name: string
    email: string
  }
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