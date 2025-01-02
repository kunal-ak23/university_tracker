import { notFound } from "next/navigation"
import { getPayment } from "@/service/api/payments"
import { Badge } from "@/components/ui/badge"
import { Calendar, IndianRupee } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default async function PaymentPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  let payment;
  const {id} = await params
  try {
    payment = await getPayment(String(id));
  } catch (error) {
    console.error('Error fetching payment:', error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Payment #{payment.id}</h2>
        <Link href={`/payments/${payment.id}/edit`}>
          <Button>Edit Payment</Button>
        </Link>
      </div>

      <div className="grid gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Amount</p>
              <div className="flex items-center gap-1 text-2xl font-bold">
                <IndianRupee className="h-6 w-6" />
                {parseFloat(payment.amount.toString()).toLocaleString('en-IN')}
              </div>
            </div>
            <Badge variant="outline" className="text-base">
              {payment.payment_method}
            </Badge>
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            {new Date(payment.payment_date).toLocaleDateString()}
          </div>

          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Transaction ID</p>
            <p className="font-medium">{payment.transaction_reference || "-"}</p>
          </div>

          {payment.notes && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Notes</p>
              <p className="text-sm">{payment.notes}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 