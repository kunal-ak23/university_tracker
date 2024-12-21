export interface OEM {
  id: string
  name: string
  website: string
  contact_email?: string
  contact_phone?: string
  address?: string
  poc?: {
    id: string
    name: string
    email: string
  }
  created_at: string
  updated_at: string
}

export interface OEMFormData {
  name: string
  website: string
  contact_email?: string
  contact_phone?: string
  address?: string
  poc_id?: string
} 