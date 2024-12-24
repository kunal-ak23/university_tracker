import { ProgramFormData } from "@/types/program"
import { Program } from "@/types/program"
import { apiFetch } from "./fetch"
import { PaginatedResponse } from "@/types/common"

export async function getPrograms(params?: {
  page?: number
  search?: string
  ordering?: string
  page_size?: number
  provider?: number
  oem?: number | string
}): Promise<PaginatedResponse<Program>> {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.set("page", params.page.toString())
  if (params?.search) searchParams.set("search", params.search)
  if (params?.ordering) searchParams.set("ordering", params.ordering)
  if (params?.page_size) searchParams.set("page_size", params.page_size.toString())
  if (params?.provider) searchParams.set("provider", params.provider.toString())
  if (params?.oem) searchParams.set("oem", params.oem.toString())

  const queryString = searchParams.toString()
  const url = `/programs/${queryString ? `?${queryString}` : ""}`
  
  return apiFetch(url)
}

export async function getProgram(id: number): Promise<Program> {
  return apiFetch(`/programs/${id}/`)
}

export async function createProgram(data: ProgramFormData): Promise<Program> {
  return apiFetch("/programs/", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function updateProgram(id: number, data: ProgramFormData): Promise<Program> {
  return apiFetch(`/programs/${id}/`, {
    method: "PATCH",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function deleteProgram(id: number): Promise<void> {
  return apiFetch(`/programs/${id}/`, {
    method: "DELETE",
  })
}

export async function getProgramsByOem(oemId: string | number): Promise<PaginatedResponse<Program>> {
  return getPrograms({ oem: oemId })
} 