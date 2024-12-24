import { getBilling } from "@/service/api/billings"
import { notFound } from "next/navigation"
import { BillingDetails } from "@/components/billings/billing-details"

export default async function BillingPage({
  params,
}: {
  params: { id: string }
}) {
  let billing;
  try {
    billing = await getBilling(params.id)
  } catch (error) {
    console.error('Error fetching billing:', error)
    notFound()
  }

  return <BillingDetails billing={billing} />
} 
