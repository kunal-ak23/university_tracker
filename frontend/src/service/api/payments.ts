import { Payment, PaymentFormData } from "@/types/payment"
import { PaginatedResponse } from "@/types/common"
import { apiFetch } from "./fetch"

export async function getPayments(params?: {
  page?: number
  search?: string
  invoice?: string
}): Promise<PaginatedResponse<Payment>> {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.set("page", params.page.toString())
  if (params?.search) searchParams.set("search", params.search)
  if (params?.invoice) searchParams.set("invoice", params.invoice)

  return apiFetch(`/payments/?${searchParams.toString()}`)
}

export async function getPayment(id: string): Promise<Payment> {
  return apiFetch(`/payments/${id}/`)
}

export async function createPayment(data: PaymentFormData): Promise<Payment> {
  return apiFetch("/payments/", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function updatePayment(id: string, data: PaymentFormData): Promise<Payment> {
  return apiFetch(`/payments/${id}/`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export async function deletePayment(id: string): Promise<void> {
  return apiFetch(`/payments/${id}/`, {
    method: "DELETE",
  })
} 