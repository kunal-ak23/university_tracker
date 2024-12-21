import { getOEMs } from "@/lib/api/oems"
import { OEMsTable } from "@/components/oems/oems-table"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"

export default async function OEMsPage() {
  const oems = (await getOEMs()).results


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">OEMs</h2>
        <Link href="/oems/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add OEM
          </Button>
        </Link>
      </div>
      <OEMsTable oems={oems} />
    </div>
  )
} 