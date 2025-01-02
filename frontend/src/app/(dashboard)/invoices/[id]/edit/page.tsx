import { getInvoice } from "@/service/api/invoices"
import { InvoiceForm } from "@/components/forms/invoice/invoice-form"
import { PageHeader } from "@/components/page-header"


export default async function EditInvoicePage({params}: {params: Promise<{
    id: string
  }>}) {
    const {id} = await params;
    const invoice = await getInvoice(Number(id))

  return (
    <div className="container mx-auto py-10">
      <PageHeader
        title="Edit Invoice"
        description="Update invoice details"
      />
      <div className="mt-8">
        <InvoiceForm invoice={invoice} />
      </div>
    </div>
  )
} 