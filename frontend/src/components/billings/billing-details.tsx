"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { Pencil, IndianRupee, Receipt, Users, Percent } from "lucide-react"
import { BillingActions } from "@/app/(dashboard)/billings/[id]/actions"
import { Billing } from "@/types/billing"

interface BillingDetailsProps {
  billing: Billing
}

function getStatusBadgeVariant(status: string, balanceDue: string) {
  switch (status) {
    case 'draft':
      return 'outline'
    case 'archived':
      return 'secondary'
    case 'active':
      return parseFloat(balanceDue) > 0 ? 'destructive' : 'default'
    default:
      return 'default'
  }
}

function getStatusLabel(status: string, balanceDue: string) {
  switch (status) {
    case 'draft':
      return 'Draft'
    case 'archived':
      return 'Archived'
    case 'active':
      return parseFloat(balanceDue) > 0 ? 'Active (Outstanding)' : 'Paid'
    default:
      return status
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

export function BillingDetails({ billing }: BillingDetailsProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-3xl font-bold tracking-tight">{billing.name}</h2>
          <Badge variant={getStatusBadgeVariant(billing.status, billing.balance_due)}>
            {getStatusLabel(billing.status, billing.balance_due)}
          </Badge>
        </div>
        <div className="flex gap-4">
          <BillingActions billing={billing} />
          <Link href={`/billings/${billing.id}/edit`}>
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
          <div className="space-y-1">
            <p className="text-2xl font-bold">₹{parseFloat(billing.total_amount).toLocaleString('en-IN')}</p>
            <p className="text-sm text-gray-500">Base: ₹{(parseFloat(billing.total_amount) / (1 + parseFloat(billing.batch_snapshots[0]?.tax_rate || "0") / 100)).toLocaleString('en-IN')}</p>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Percent className="h-3 w-3" />
              <span>Tax: {billing.batch_snapshots[0]?.tax_rate}%</span>
            </div>
          </div>
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
          <div className="space-y-1">
            <p className="text-2xl font-bold">₹{parseFloat(billing.total_oem_transfer_amount).toLocaleString('en-IN')}</p>
            <p className="text-sm text-gray-500">Base: ₹{(parseFloat(billing.total_oem_transfer_amount) / (1 + parseFloat(billing.batch_snapshots[0]?.tax_rate || "0") / 100)).toLocaleString('en-IN')}</p>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Percent className="h-3 w-3" />
              <span>Tax: {billing.batch_snapshots[0]?.tax_rate}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Batches Section */}
      <div className="rounded-lg border p-6 space-y-4">
        <h3 className="text-xl font-semibold">Included Batches</h3>
        <div className="grid grid-cols-3 gap-4">
          {billing.batch_snapshots.map((batch, index) => (
            <div key={"batch-" + index} className="rounded-lg border p-4 space-y-3">
              <div className="flex justify-between items-start">
                <h4 className="font-semibold">{batch.batch_name}</h4>
                <Badge variant="secondary">
                  {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Users className="h-4 w-4" />
                  {batch.number_of_students} students
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Percent className="h-4 w-4" />
                  Tax Rate: {batch.tax_rate}%
                </div>
                <div className="col-span-2 flex items-center gap-2 text-sm text-gray-600">
                  <IndianRupee className="h-4 w-4" />
                  Base Cost: ₹{parseFloat(batch.cost_per_student).toLocaleString('en-IN')} per student
                </div>
                <div className="col-span-2 flex items-center gap-2 text-sm text-gray-600">
                  <IndianRupee className="h-4 w-4" />
                  With Tax: ₹{(parseFloat(batch.cost_per_student) * (1 + parseFloat(batch.tax_rate) / 100)).toLocaleString('en-IN')} per student
                </div>
                <div className="col-span-2 border-t pt-2">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Base Total:</span>
                      <span>₹{(batch.number_of_students * parseFloat(batch.cost_per_student)).toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Tax Amount:</span>
                      <span>₹{(batch.number_of_students * parseFloat(batch.cost_per_student) * parseFloat(batch.tax_rate) / 100).toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm font-medium">
                      <span>Total with Tax:</span>
                      <span>₹{(batch.number_of_students * parseFloat(batch.cost_per_student) * (1 + parseFloat(batch.tax_rate) / 100)).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </div>
                <div className="col-span-2 border-t pt-2">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Base OEM Transfer:</span>
                      <span>₹{(batch.number_of_students * parseFloat(batch.oem_transfer_price)).toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Tax Amount:</span>
                      <span>₹{(batch.number_of_students * parseFloat(batch.oem_transfer_price) * parseFloat(batch.tax_rate) / 100).toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm font-medium">
                      <span>OEM Total with Tax:</span>
                      <span>₹{(batch.number_of_students * parseFloat(batch.oem_transfer_price) * (1 + parseFloat(batch.tax_rate) / 100)).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Stream: {batch.batch_stream}
              </div>
              <div className="pt-2">
                <Link href={`/batches/${batch.batch}`}>
                  <Button variant="ghost" size="sm" className="w-full">
                    View Source Batch
                  </Button>
                </Link>
              </div>
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
              <Badge variant={getStatusBadgeVariant(billing.status, billing.balance_due)}>
                {getStatusLabel(billing.status, billing.balance_due)}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd>{formatDate(billing.created_at)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
            <dd>{formatDate(billing.updated_at)}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
} 
