import { PaginatedResponse } from "@/types/common"
import { apiFetch } from "./fetch"

export interface TaxRate {
  id: string
  rate: number
  name: string
}

export async function getTaxRates(): Promise<PaginatedResponse<TaxRate>> {
  return apiFetch('/tax-rates/')
}

export async function getDefaultTaxRate(): Promise<TaxRate> {
  return apiFetch('/tax-rates/1/')
} 