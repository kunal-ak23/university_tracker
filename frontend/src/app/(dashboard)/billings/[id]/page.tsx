import { getBilling } from "@/service/api/billings"
import { notFound } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { Pencil, IndianRupee, Calendar, Receipt } from "lucide-react"

export default async function BillingPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  let billing;
  const {id} = await params
  try {
    billing = await getBilling(id)
    console.log(billing);

  } catch (error) {
    console.error('Error fetching billing:', error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{billing.name}</h2>
        <div className="flex gap-4">
          <Link href={`/billings/${id}/edit`}>
            <Button>
              <Pencil className="mr-2 h-4 w-4" />
              Edit Billing
            </Button>
          </Link>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <IndianRupee className="h-4 w-4" />
            <h4 className="font-medium">Total Amount</h4>
          </div>
          <p className="text-2xl font-bold">₹{parseFloat(billing.total_amount).toLocaleString('en-IN')}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Receipt className="h-4 w-4" />
            <h4 className="font-medium">Total Payments</h4>
          </div>
          <p className="text-2xl font-bold">₹{parseFloat(billing.total_payments).toLocaleString('en-IN')}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <IndianRupee className="h-4 w-4" />
            <h4 className="font-medium">Balance Due</h4>
          </div>
          <p className="text-2xl font-bold">₹{parseFloat(billing.balance_due).toLocaleString('en-IN')}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <IndianRupee className="h-4 w-4" />
            <h4 className="font-medium">OEM Transfer</h4>
          </div>
          <p className="text-2xl font-bold">₹{parseFloat(billing.total_oem_transfer_amount).toLocaleString('en-IN')}</p>
        </div>
      </div>

      {/* Batches Section */}
      <div className="rounded-lg border p-6 space-y-4">
        <h3 className="text-xl font-semibold">Included Batches</h3>
        <div className="grid grid-cols-3 gap-4">
          {billing.batch_snapshots.map((batch, index) => (
            <div key={"batch-" + index} className="rounded-lg border p-4 space-y-2">
              <h4 className="font-semibold">{batch.batch_name}</h4>
              <Link href={`/batches/${batch.id}`}>
                <Button variant="ghost" size="sm" className="w-full">
                  View Batch
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Notes Section */}
      {billing.notes && (
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Notes</h3>
          <p className="text-gray-600 whitespace-pre-line">{billing.notes}</p>
        </div>
      )}

      {/* Metadata Section */}
      <div className="rounded-lg border p-6 space-y-4">
        <h3 className="text-xl font-semibold">Details</h3>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd>
              <Badge variant={parseFloat(billing.balance_due) > 0 ? "destructive" : "secondary"}>
                {parseFloat(billing.balance_due) > 0 ? 'Pending' : 'Paid'}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd>{new Date(billing.created_at).toLocaleDateString()}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
            <dd>{new Date(billing.updated_at).toLocaleDateString()}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
} 
