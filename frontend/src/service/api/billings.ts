import {Billing, BillingCreateInput} from "@/types/billing"
import {PaginatedResponse} from "@/types/common"
import {apiFetch} from "./fetch"

interface GetBillingsParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  ordering?: string
}

export async function getBillings(params: GetBillingsParams = {}): Promise<PaginatedResponse<Billing>> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.append('page', params.page.toString())
  if (params.page_size) searchParams.append('page_size', params.page_size.toString())
  if (params.search) searchParams.append('search', params.search)
  if (params.status) searchParams.append('status', params.status)
  if (params.ordering) searchParams.append('ordering', params.ordering)

  return apiFetch(`/billings/?${searchParams.toString()}`)
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

export async function publishBilling(id: string): Promise<void> {
  return apiFetch(`/billings/${id}/publish/`, {
    method: "POST",
  })
}

export async function archiveBilling(id: string): Promise<void> {
  return apiFetch(`/billings/${id}/archive/`, {
    method: "POST",
  })
}

export async function deleteBilling(id: string): Promise<void> {
  return apiFetch(`/billings/${id}/`, {
    method: "DELETE",
  })
} 
