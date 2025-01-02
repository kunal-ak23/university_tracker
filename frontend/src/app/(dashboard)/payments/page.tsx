import { Plus } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { PaymentList } from "@/components/payments/payment-list"
import { getPayments } from "@/service/api/payments"
import { PaymentsSearch } from "@/components/payments/payments-search"

export default async function PaymentsPage({
  params,
}: {params: Promise<{page?: string, search?: string}>}) {
  
  const {page, search} = await params;
  const pageNumber = Number(page) || 1
  const searchString = search || ""
  const response = await getPayments({ page: pageNumber, search: searchString })
  const totalPages = Math.ceil(response.count / 10)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Payments</h2>
        <Link href="/payments/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Payment
          </Button>
        </Link>
      </div>

      <PaymentsSearch 
        initialSearch={searchString}
        initialPage={pageNumber}
        totalPages={totalPages}
        totalCount={response.count}
      />

      <PaymentList payments={response.results} />
    </div>
  )
} 