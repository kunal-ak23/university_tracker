import { getBillings } from "@/service/api/billings"
import { Plus, IndianRupee } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default async function BillingsPage() {
  const { results: billings } = await getBillings()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Billings</h2>
        <Link href="/billings/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Billing
          </Button>
        </Link>
      </div>

      <div className="grid gap-4">
        {billings.map((billing) => (
          <div
            key={billing.id}
            className="rounded-lg border p-4"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">{billing.name}</h3>
                {billing.notes && (
                  <p className="mt-1 text-sm text-gray-600">{billing.notes}</p>
                )}
              </div>
              <Badge variant={parseFloat(billing.balance_due) > 0 ? "destructive" : "secondary"}>
                {parseFloat(billing.balance_due) > 0 ? 'Pending' : 'Paid'}
              </Badge>
            </div>
            
            <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Total Amount</p>
                <p className="font-medium">₹{parseFloat(billing.total_amount).toLocaleString('en-IN')}</p>
              </div>
              <div>
                <p className="text-gray-600">Total Payments</p>
                <p className="font-medium">₹{parseFloat(billing.total_payments).toLocaleString('en-IN')}</p>
              </div>
              <div>
                <p className="text-gray-600">Balance Due</p>
                <p className="font-medium">₹{parseFloat(billing.balance_due).toLocaleString('en-IN')}</p>
              </div>
              <div>
                <p className="text-gray-600">OEM Transfer Amount</p>
                <p className="font-medium">₹{parseFloat(billing.total_oem_transfer_amount).toLocaleString('en-IN')}</p>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Created on {new Date(billing.created_at).toLocaleDateString()}
              </div>
              <Link href={`/billings/${billing.id}`}>
                <Button variant="outline" size="sm">
                  View Details
                </Button>
              </Link>
            </div>
          </div>
        ))}

        {billings.length === 0 && (
          <div className="rounded-lg border border-dashed p-8">
            <div className="text-center">
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No billings</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating a new billing.</p>
              <div className="mt-6">
                <Link href="/billings/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Billing
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 
