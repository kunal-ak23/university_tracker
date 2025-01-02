import { PaginatedResponse } from "@/types/api"
import { Invoice } from "@/types/payment"
import { apiFetch, postFormData } from "./fetch"

interface GetInvoicesParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
}

export async function getInvoices(params: GetInvoicesParams = {}): Promise<PaginatedResponse<Invoice>> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.append('page', params.page.toString())
  if (params.page_size) searchParams.append('page_size', params.page_size.toString())
  if (params.search) searchParams.append('search', params.search)
  if (params.ordering) searchParams.append('ordering', params.ordering)

  return apiFetch(`/invoices/?${searchParams.toString()}`)
}

export async function getInvoice(id: number): Promise<Invoice> {
  return apiFetch(`/invoices/${id}/`)
}

export async function createInvoice(data: FormData): Promise<Invoice> {
  return postFormData('/invoices/', data, {
    method: 'POST',
  })
}

export async function updateInvoice(id: number, data: FormData): Promise<Invoice> {
  return postFormData(`/invoices/${id}/`, data, {
    method: 'PATCH',
  })
}

export async function deleteInvoice(id: number): Promise<void> {
  return apiFetch(`/invoices/${id}/`, {
    method: 'DELETE',
  })
}

export async function sendInvoice(id: number): Promise<void> {
  return apiFetch(`/invoices/${id}/send/`, {
    method: 'POST',
  })
}
