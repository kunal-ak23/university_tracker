import { getContract } from "@/lib/api/contracts"
import { notFound } from "next/navigation"
import { ContractForm } from "@/components/forms/contract/contract-form"

interface EditContractPageProps {
  params: Promise<{
    id: string
  }>
}

export default async function EditContractPage({ params }: EditContractPageProps) {
  const { id } = await params
  let contract
  try {
    contract = await getContract(id)
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