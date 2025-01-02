import { InvoiceForm } from "@/components/forms/invoice/invoice-form"

export default function NewInvoicePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Create New Invoice</h2>
        <p className="text-muted-foreground mt-2">
          Create a new invoice by filling out the form below.
        </p>
      </div>
      <InvoiceForm />
    </div>
  )
} 