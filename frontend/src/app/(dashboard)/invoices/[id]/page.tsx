import { getInvoice } from "@/service/api/invoices"
import { InvoiceDetails } from "@/components/invoices/invoice-details"


export default async function InvoiceDetailsPage({ params }: {params: Promise<{
  id: string
}>}) {
  const {id} = await params;
  const invoice = await getInvoice(Number(id))

  return (
    <div className="container mx-auto">
        <InvoiceDetails invoice={invoice} />
    </div>
  )
  
} 