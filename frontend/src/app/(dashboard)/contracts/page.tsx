import { ContractsTable } from "@/components/contracts/contracts-table"
import { Button } from "@/components/ui/button"
import { getContracts } from "@/lib/api/contracts"
import { Plus } from "lucide-react"
import Link from "next/link"

export default async function ContractsPage() {
  const contracts = (await getContracts()).results

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Contracts</h2>
        <div>
        <Link href="/contracts/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Contract
          </Button>
        </Link>
        </div>
      </div>
      <ContractsTable contracts={contracts} />
    </div>
  )
} 