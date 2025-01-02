import { Suspense } from "react"
import { InvoicesList } from "./invoices-list"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"

export default function InvoicesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Invoices</h2>
        <Link href="/invoices/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create Invoice
          </Button>
        </Link>
      </div>
      <Suspense fallback={<div className="flex items-center justify-center h-24">Loading...</div>}>
        <InvoicesList />
      </Suspense>
    </div>
  )
} 