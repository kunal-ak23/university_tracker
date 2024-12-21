"use server"

import { getContract } from "@/lib/api/contracts"
import { notFound } from "next/navigation"
import { ContractForm } from "@/components/forms/contract/contract-form"

export default async function EditContractPage({
  params,
}: {
  params: { id: string }
}) {
  let contract
  const id = {params};
  try {
    contract = await getContract(id.toString());
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Edit Contract</h2>
      </div>
      <ContractForm mode="edit" contract={contract} />
    </div>
  )
} 