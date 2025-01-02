import { BillingDetails } from "@/components/billings/billing-details";
import { getBilling } from "@/service/api/billings"
import { notFound } from "next/navigation"


export default async function BillingPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  let billing;
  const {id} = await params
  try {
    billing = await getBilling(id)
  } catch (error) {
    console.error('Error fetching billing:', error)
    notFound()
  }

  return <BillingDetails billing={billing} />
} 
