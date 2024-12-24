import { Batch } from "@/types/batch"
import { apiFetch } from "./fetch"
import { BatchFormValues } from "@/components/batches/batch-form"
import { PaginatedResponse } from "@/types/common"

export async function getBatches(url = '/batches/'): Promise<PaginatedResponse<Batch>> {
  return apiFetch(url)
}

export async function getBatchesByStream(streamId: string): Promise<PaginatedResponse<Batch>> {
  return apiFetch(`/batches/?stream=${streamId}`)
}

export async function getBatch(id: string): Promise<Batch> {
  return apiFetch(`/batches/${id}/`)
}

export async function createBatch(data: BatchFormValues): Promise<Batch> {
  return apiFetch('/batches/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function updateBatch(id: string, data: BatchFormValues): Promise<Batch> {
  return apiFetch(`/batches/${id}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function deleteBatch(id: string): Promise<void> {
  return apiFetch(`/batches/${id}/`, {
    method: 'DELETE',
  })
} 