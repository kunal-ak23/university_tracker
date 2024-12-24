import {Billing, BillingCreateInput} from "@/types/billing"
import {PaginatedResponse} from "@/types/common"
import {apiFetch} from "./fetch"

export async function getBillings(params?: {
  page?: number
  search?: string
  ordering?: string
}): Promise<PaginatedResponse<Billing>> {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.set("page", params.page.toString())
  if (params?.search) searchParams.set("search", params.search)
  if (params?.ordering) searchParams.set("ordering", params.ordering)

  const queryString = searchParams.toString()
  const url = `/billings/${queryString ? `?${queryString}` : ""}`
  
  return apiFetch(url)
}

export async function getBilling(id: string): Promise<Billing> {
  return apiFetch(`/billings/${id}/`)
}

export async function createBilling(data: BillingCreateInput): Promise<Billing> {
  return apiFetch("/billings/", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function updateBilling(id: string, data: Partial<BillingCreateInput>): Promise<Billing> {
  return apiFetch(`/billings/${id}/`, {
    method: "PATCH",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function deleteBilling(id: string): Promise<void> {
  return apiFetch(`/billings/${id}/`, {
    method: "DELETE",
  })
} 
