import { notFound } from "next/navigation"
import { PaymentForm } from "@/components/forms/payment/payment-form"
import { getPayment } from "@/service/api/payments"
import { getInvoices } from "@/service/api/invoices"

export default async function EditPaymentPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  let payment;
  const {id} = await params
  try {
    payment = await getPayment(id)
  } catch (error) {
    console.error('Error fetching payment:', error)
    notFound()
  }

  const { results: invoices } = await getInvoices()

  return (
    <div className="space-y-4">
      <h2 className="text-3xl font-bold tracking-tight">Edit Payment</h2>
      <PaymentForm mode="edit" payment={payment} invoices={invoices} />
    </div>
  )
} 