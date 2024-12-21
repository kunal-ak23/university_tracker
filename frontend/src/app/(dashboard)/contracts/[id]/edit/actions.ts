'use server'

import { updateContract } from "@/lib/api/contracts"
import { ContractFormData } from "@/types/contract"

export async function handleUpdateContract({ id, formData }: { id: string, formData: ContractFormData }) {
  try {
    const data = {
      ...formData,
      tax_rate: Number(formData.tax_rate),
      oem_id: Number(formData.oem_id),
      university_id: Number(formData.university_id),
      streams_ids: formData.streams_ids,
      programs_ids: formData.programs_ids
    }

    console.log(data)
    
    await updateContract(id, data)
  } catch (error) {
    console.error('Failed to update contract:', error)
    throw error
  }
}
