import { ContractForm } from "@/components/forms/contract/contract-form"

export default function NewContractPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New Contract</h2>
      </div>
      <ContractForm />
    </div>
  )
} 