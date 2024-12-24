"use client"

import { Billing } from "@/types/billing"
import { Badge } from "@/components/ui/badge"
import { IndianRupee } from "lucide-react"
import Link from "next/link"

interface BillingListProps {
  billings: Billing[]
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

export function BillingList({ billings }: BillingListProps) {
  return (
    <div className="space-y-4">
      {billings.map((billing) => (
        <Link
          key={billing.id}
          href={`/billings/${billing.id}`}
          className="block"
        >
          <div className="rounded-lg border p-4 transition-colors hover:bg-muted/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h3 className="font-semibold">{billing.name}</h3>
                <Badge variant={getStatusBadgeVariant(billing.status, billing.balance_due)}>
                  {getStatusLabel(billing.status, billing.balance_due)}
                </Badge>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Total Amount</p>
                  <div className="flex items-center gap-1 font-medium">
                    <IndianRupee className="h-4 w-4" />
                    {parseFloat(billing.total_amount).toLocaleString('en-IN')}
                  </div>
                </div>
                {billing.status === 'active' && (
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Balance Due</p>
                    <div className="flex items-center gap-1 font-medium">
                      <IndianRupee className="h-4 w-4" />
                      {parseFloat(billing.balance_due).toLocaleString('en-IN')}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              {billing.batch_snapshots.length} batches • Created on {formatDate(billing.created_at)}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
} 