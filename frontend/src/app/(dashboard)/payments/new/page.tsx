import { PaymentForm } from "@/components/forms/payment/payment-form"
import { getInvoices } from "@/service/api/invoices"


export default async function NewPaymentPage() {
  const invoices = (await getInvoices()).results

  return (
    <div className="space-y-4">
      <h2 className="text-3xl font-bold tracking-tight">New Payment</h2>
      <PaymentForm invoices={invoices} />
    </div>
  )
} 