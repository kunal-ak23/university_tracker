'use server'

import { apiFetch, postFormData } from "@/lib/api/fetch"

export async function handleContractFileUpload(formData: FormData) {
    console.log(formData);
  try {
    return await postFormData('/contract-files/', formData)
  } catch (error) {
    console.error('Failed to upload contract file:', error)
    throw error
  }
}

export async function handleContractFileDelete(fileId: number) {
  console.log("Deleting file:", fileId)
  try {
    await apiFetch(`/contract-files/${fileId}/`, {
      method: 'DELETE',
    })
    console.log("File deleted successfully")
  } catch (error) {
    console.error("Delete failed:", error)
    throw error
  }
} 