'use server'

import { apiFetch, postFormData } from "@/service/api/fetch"

export async function handleContractFileUpload(formData: FormData) {
  try {
    return await postFormData('/contract-files/', formData)
  } catch (error) {
    console.error('Failed to upload contract file:', error)
    throw error
  }
}

export async function handleContractFileDelete(fileId: number) {
  try {
    await apiFetch(`/contract-files/${fileId}/`, {
      method: 'DELETE',
    })
  } catch (error) {
    console.error("Delete failed:", error)
    throw error
  }
} 
