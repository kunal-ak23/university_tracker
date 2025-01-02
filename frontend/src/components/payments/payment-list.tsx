import { Payment } from "@/types/payment"
import { Badge } from "@/components/ui/badge"
import { Calendar, IndianRupee } from "lucide-react"
import Link from "next/link"

interface PaymentListProps {
  payments: Payment[]
}

export function PaymentList({ payments }: PaymentListProps) {
  return (
    <div className="space-y-4">
      {payments.map((payment) => (
        <Link key={payment.id} href={`/payments/${payment.id}`} className="block">
          <div className="rounded-lg border p-4 transition-colors hover:bg-muted/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h3 className="font-semibold">Payment #{payment.id}</h3>
                <Badge variant="outline">
                  {payment.payment_method}
                </Badge>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Amount</p>
                  <div className="flex items-center gap-1 font-medium">
                    <IndianRupee className="h-4 w-4" />
                    {payment.amount.toLocaleString('en-IN')}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              {new Date(payment.payment_date).toLocaleDateString()}
              {payment.transaction_reference && (
                <span className="ml-2">• Transaction Reference: {payment.transaction_reference}</span>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
} 