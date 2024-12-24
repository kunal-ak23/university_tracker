import {Billing, BillingCreateInput} from "@/types/billing"
import {PaginatedResponse} from "@/types/common"
import {apiFetch} from "./fetch"

export async function getBillings(params?: {
  page?: number
  search?: string
  ordering?: string
  status?: string
}): Promise<PaginatedResponse<Billing>> {
  const searchParams = new URLSearchParams()
  console.log("params", params);
  console.log("params.page", params?.page);


  if(params?.status) searchParams.set("status", params.status);
  if (params?.page) searchParams.set("page", params.page.toString())
  if (params?.search) searchParams.set("search", params.search)
  if (params?.ordering) searchParams.set("ordering", params.ordering)

  const queryString = searchParams.toString()
  console.log("queryString", queryString);
  const url = `/billings/${queryString ? `?${queryString}` : ""}`
  
  console.log("url", url);
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

export async function publishBilling(id: string): Promise<void> {
  console.log("publishBilling", id);
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
