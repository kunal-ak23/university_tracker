import { getBillings } from "@/service/api/billings"
import { Plus } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { BillingTabs } from "@/components/billings/billing-tabs"

function BillingsHeader({ status }: { status: string }) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="text-3xl font-bold tracking-tight">Billings</h2>
      <Link href="/billings/new">
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create Billing
        </Button>
      </Link>
    </div>
  )
}

export default async function BillingsPage({
  searchParams,
}: {
  searchParams: { status?: string }
}) {
  // Get initial data for the active tab
  const status = searchParams.status || 'active'
  const { results: initialBillings } = await getBillings({ status })

  return (
    <div className="space-y-6">
      <BillingsHeader status={status} />
      <BillingTabs defaultStatus={status} initialBillings={initialBillings} />
    </div>
  )
} 
