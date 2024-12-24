import { getContract } from "@/service/api/contracts"
import { notFound } from "next/navigation"

import { ContractFilesForm } from "@/components/contracts/contract-files-form"
import { handleContractFileUpload, handleContractFileDelete } from "./actions";

export default async function ContractFilesPage({
    params,
}: Readonly<{
  params: Promise<{ id: string }>;
}>) {
  const { id } = await params;
  let contract;
  try {
    contract = await getContract(id)
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Manage Contract Files</h2>
        <span className="text-muted-foreground">Contract: {contract.name}</span>
      </div>
      <ContractFilesForm 
        contract={contract}
        action={{
          upload: handleContractFileUpload,
          delete: handleContractFileDelete
        }}
      />
    </div>
  )
} 
