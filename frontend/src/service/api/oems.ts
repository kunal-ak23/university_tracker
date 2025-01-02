import { OEM, OEMFormData } from "@/types/oem"
import { apiFetch } from "./fetch"
import { PaginatedResponse } from "@/types/common";

interface GetOEMsParams {
  page?: number
  search?: string
  page_size?: number
  ordering?: string
}

export async function getOEMs(params?: GetOEMsParams): Promise<PaginatedResponse<OEM>> {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.append('page', params.page.toString())
  if (params?.search) searchParams.append('search', params.search)
  if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
  if (params?.ordering) searchParams.append('ordering', params.ordering)
  
  const queryString = searchParams.toString()
  const url = `/oems/${queryString ? `?${queryString}` : ''}`
  return apiFetch(url)
}

export async function getOEM(id: string): Promise<OEM> {
  return apiFetch(`/oems/${id}/`)
}

export async function createOEM(data: OEMFormData): Promise<OEM> {
  return apiFetch('/oems/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function updateOEM(id: string, data: OEMFormData): Promise<OEM> {
    return apiFetch(`/oems/${id}/`, {
        method: 'PATCH',
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
}

export async function deleteOEM(id: string): Promise<void> {
  return apiFetch(`/oems/${id}/`, {
    method: 'DELETE',
  })
}

export interface Program {
  id: string
  name: string
  program_code: string
  duration: number
  duration_unit: string
}

export async function getOEMPrograms(oemId: string): Promise<PaginatedResponse<Program>> {
  return apiFetch(`/programs/?oem=${oemId}`)
} 