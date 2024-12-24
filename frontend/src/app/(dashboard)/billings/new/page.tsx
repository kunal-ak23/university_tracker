import { BillingForm } from "@/components/forms/billing/billing-form"
import { getBatches } from "@/service/api/batches"

export default async function NewBillingPage() {
  const { results: batches } = await getBatches()

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Create New Billing</h2>
        <p className="text-muted-foreground">
          Create a new billing by selecting batches and providing billing details.
        </p>
      </div>

      <div className="rounded-lg border p-6">
        <BillingForm
          mode="create"
          availableBatches={batches}
        />
      </div>
    </div>
  )
} 
