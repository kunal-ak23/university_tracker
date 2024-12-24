import { getBilling } from "@/service/api/billings"
import { getBatches } from "@/service/api/batches"
import { BillingForm } from "@/components/forms/billing/billing-form"
import { notFound } from "next/navigation"

export default async function EditBillingPage({
  params,
}: {
  params: { id: string }
}) {
  let billing;
  try {
    const [billingData, batchesData] = await Promise.all([
      getBilling(params.id),
      getBatches()
    ])
    billing = billingData
    const batches = batchesData.results

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Edit Billing</h2>
          <p className="text-muted-foreground">
            Update billing details and manage associated batches.
          </p>
        </div>

        <div className="rounded-lg border p-6">
          <BillingForm
            mode="edit"
            billing={billing}
            availableBatches={batches.map(batch => ({
              id: batch.id.toString(),
              name: batch.name
            }))}
          />
        </div>
      </div>
    )
  } catch (error) {
    console.error('Error fetching billing:', error)
    notFound()
  }
} 
