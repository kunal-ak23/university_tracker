"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { formatDate, formatCurrency } from "@/service/utils"
import { FileText, Plus, Edit, Trash2 } from "lucide-react"
import { PaymentDialog } from "../payments/payment-dialog"
import { PaymentsTable } from "../payments/payments-table"
import { deleteInvoice } from "@/service/api/invoices"
import { useToast } from "@/hooks/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Invoice } from "@/types/payment"


interface InvoiceDetailsProps {
  invoice: Invoice
}

export function InvoiceDetails({ invoice }: InvoiceDetailsProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [isPaymentDialogOpen, setIsPaymentDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const remainingAmount = Number(invoice.amount) - Number(invoice.amount_paid)

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await deleteInvoice(invoice.id)
      toast({
        title: "Success",
        description: "Invoice deleted successfully",
      })
      router.push('/invoices')
      router.refresh()
    } catch (error) {
      console.error("Failed to delete invoice:", error)
      toast({
        title: "Error",
        description: "Failed to delete invoice",
        variant: "destructive",
      })
    } finally {
      setIsDeleting(false)
      setIsDeleteDialogOpen(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{invoice.name}</h2>
          <p className="text-sm text-muted-foreground">Invoice #{invoice.id}</p>
        </div>
        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={() => router.push(`/invoices/${invoice.id}/edit`)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button
            variant="destructive"
            onClick={() => setIsDeleteDialogOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Invoice Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Name</div>
                <div className="font-medium">{invoice.name}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Billing</div>
                {/* <div className="font-medium">{invoice.billing_name}</div> */}
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Status</div>
                <Badge>{invoice.status}</Badge>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Issue Date</div>
                <div className="font-medium">{formatDate(invoice.issue_date)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Due Date</div>
                <div className="font-medium">{formatDate(invoice.due_date)}</div>
              </div>
            </div>
            {invoice.notes && (
              <>
                <Separator />
                <div>
                  <div className="text-sm text-muted-foreground">Notes</div>
                  <div className="mt-1 whitespace-pre-wrap">{invoice.notes}</div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payment Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Total Amount</div>
                <div className="font-medium">{formatCurrency(parseFloat(invoice.amount))}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Amount Paid</div>
                <div className="font-medium">{formatCurrency(parseFloat(invoice.amount_paid))}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Remaining Amount</div>
                <div className="font-medium">{formatCurrency(remainingAmount)}</div>
              </div>
            </div>
            <div className="flex gap-4">
              {invoice.proforma_invoice && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL}/invoices/${invoice.id}/proforma/`, '_blank')}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  View Proforma Invoice
                </Button>
              )}
              {invoice.actual_invoice && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL}/invoices/${invoice.id}/actual/`, '_blank')}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  View Actual Invoice
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Payments</CardTitle>
          <Button
            onClick={() => setIsPaymentDialogOpen(true)}
            disabled={remainingAmount <= 0}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Payment
          </Button>
        </CardHeader>
        <CardContent>
          <PaymentsTable
            payments={invoice.payments || []}
            onPaymentDeleted={() => router.refresh()}
            onPaymentUpdated={() => router.refresh()}
          />
        </CardContent>
      </Card>

      <PaymentDialog
        open={isPaymentDialogOpen}
        onOpenChange={setIsPaymentDialogOpen}
        invoiceId={invoice.id}
        maxAmount={remainingAmount}
        onPaymentAdded={() => {
          setIsPaymentDialogOpen(false)
          router.refresh()
        }}
      />

      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Invoice</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this invoice? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
} 