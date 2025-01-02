import { University, UniversityFormData } from "@/types/university"
import { apiFetch } from "./fetch"
import { Stream } from "@/types/contract"

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

interface GetUniversitiesParams {
  page?: number
  search?: string
  page_size?: number
  ordering?: string
}

export async function getUniversities(params?: GetUniversitiesParams): Promise<PaginatedResponse<University>> {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.append('page', params.page.toString())
  if (params?.search) searchParams.append('search', params.search)
  if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
  if (params?.ordering) searchParams.append('ordering', params.ordering)
  
  const queryString = searchParams.toString()
  const url = `/universities/${queryString ? `?${queryString}` : ''}`
  return apiFetch(url)
}

export async function getUniversity(id: string): Promise<University> {
  try {
    const response = await apiFetch(`/universities/${id}/`)
    if (!response) {
      throw new Error('University not found')
    }
    return response
  } catch (error) {
    console.error('Error fetching university:', error)
    throw error
  }
}

export async function createUniversity(data: UniversityFormData): Promise<University> {
  return apiFetch('/universities/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function updateUniversity(id: string, data: UniversityFormData): Promise<University> {
  return apiFetch(`/universities/${id}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function deleteUniversity(id: string): Promise<void> {
  return apiFetch(`/universities/${id}/`, {
    method: 'DELETE',
  })
}

export async function getUniversityStreams(universityId: string): Promise<PaginatedResponse<Stream>> {
  return apiFetch(`/streams/?university=${universityId}`)
} 