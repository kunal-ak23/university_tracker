import { apiFetch } from "./fetch"
import { PaginatedResponse } from "@/types/common"

export interface User {
  id: number;
  username: string;
  email: string
  role: string
  full_name: string
  first_name: string
  last_name: string
  phone_number: string
  profile_picture: string
  is_active: boolean
  is_superuser: boolean
  is_staff: boolean
  is_provider_poc: boolean
  is_university_poc: boolean
  is_oem_poc: boolean
  is_admin: boolean
  is_superadmin: boolean
  last_login: string
  date_joined: string
  oem_pocs: number[]
  university_pocs: number[],
  date_of_birth: string,
  address: string,
  created_at: string,
  updated_at: string
}

export type POCRole = 'university' | 'provider'

export async function getEligiblePOCs(role: POCRole): Promise<PaginatedResponse<User>> {
  const roleMapping = {
    university: 'university_poc',
    provider: 'provider_poc'
  }
  
  return apiFetch(`/users/?roles=${roleMapping[role]},superuser`)
} 

export async function getUsers({page, search}: {page: number, search: string}): Promise<PaginatedResponse<User>> {
  return apiFetch(`/users/?page=${page}&search=${search}`)
}

export async function getUser(id: number): Promise<User> {
  return apiFetch(`/users/${id}/`)
}

export async function createUser(user: User): Promise<User> {
  return apiFetch(`/users/`, {
    method: 'POST',
    body: JSON.stringify(user)
  })
}

export async function updateUser(id: number, user: User): Promise<User> {
  return apiFetch(`/users/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(user)
  })
}

export async function deleteUser(id: number): Promise<void> {
  return apiFetch(`/users/${id}/`, { method: 'DELETE' })
}