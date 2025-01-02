"use client"

import { Invoice } from "@/types/payment"
import { DataTable } from "@/components/ui/data-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Edit, Trash2, Eye, Plus } from "lucide-react"
import { useRouter } from "next/navigation"
import { deleteInvoice } from "@/service/api/invoices"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/components/ui/badge"
import { formatDate, formatCurrency } from "@/service/utils"
import { ColumnDef, Row } from "@tanstack/react-table"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
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
import { useState } from "react"
import { PaymentDialog } from "../payments/payment-dialog"

interface InvoicesTableProps {
  invoices: Invoice[]
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  onSearch: (query: string) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  onDelete: (id: number) => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  hasNextPage?: boolean
  hasPreviousPage?: boolean
  totalCount: number
}

export function InvoicesTable({ 
  invoices,
  currentPage,
  totalPages,
  onPageChange,
  onDelete,
  hasNextPage,
  hasPreviousPage,
  totalCount,
}: InvoicesTableProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isPaymentDialogOpen, setIsPaymentDialogOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (!selectedInvoiceId) return
    setIsDeleting(true)
    try {
      await deleteInvoice(selectedInvoiceId)
      onDelete(selectedInvoiceId)
      toast({
        title: "Success",
        description: "Invoice deleted successfully",
      })
      router.refresh()
    } catch (error) {
      console.error(error)
      toast({
        title: "Error",
        description: "Failed to delete invoice",
        variant: "destructive",
      })
    } finally {
      setIsDeleting(false)
      setIsDeleteDialogOpen(false)
      setSelectedInvoiceId(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-100 text-green-800'
      case 'overdue':
        return 'bg-red-100 text-red-800'
      case 'sent':
        return 'bg-blue-100 text-blue-800'
      case 'draft':
        return 'bg-gray-100 text-gray-800'
      case 'cancelled':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const columns: ColumnDef<Invoice, any>[] = [
    {
      id: "id",
      header: "Invoice ID",
      accessorKey: "id",
      cell: ({ row }) => (
        <Link
          href={`/invoices/${row.original.id}`}
          className="text-blue-500 hover:underline"
        >
          {row.original.id}
        </Link>
      ),
    },
    {
      id: "name",
      header: "Name",
      accessorKey: "name",
    },
    {
      id: "billing",
      header: "Billing",
      accessorFn: (row: Invoice) => row.billing,
    },
    {
      id: "amount",
      header: "Amount",
      accessorFn: (row: Invoice) => row.amount,
      cell: ({ row }: { row: Row<Invoice> }) => formatCurrency(parseFloat(row.original.amount)),
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row: Invoice) => row.status,
      cell: ({ row }: { row: Row<Invoice> }) => (
        <Badge className={getStatusColor(row.original.status)}>
          {row.original.status.charAt(0).toUpperCase() + row.original.status.slice(1)}
        </Badge>
      ),
    },
    {
      id: "due_date",
      header: "Due Date",
      accessorFn: (row: Invoice) => row.due_date,
      cell: ({ row }: { row: Row<Invoice> }) => formatDate(row.original.due_date),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const invoice = row.original
        const remainingAmount = parseFloat(invoice.amount) - parseFloat(invoice.amount_paid)

        return (
          <TooltipProvider>
            <div className="flex gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => router.push(`/invoices/${invoice.id}`)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>View Details</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => router.push(`/invoices/${invoice.id}/edit`)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Edit Invoice</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      setSelectedInvoiceId(invoice.id)
                      setIsPaymentDialogOpen(true)
                    }}
                    disabled={remainingAmount <= 0}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Add Payment</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      setSelectedInvoiceId(invoice.id)
                      setIsDeleteDialogOpen(true)
                    }}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Delete Invoice</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        )
      },
    },
  ]

  return (
    <div>
      <DataTable<Invoice, any>
        data={invoices}
        columns={columns}
        pageCount={totalPages}
        currentPage={currentPage}
        searchPlaceholder="Search invoices..."
        hasNextPage={hasNextPage}
        hasPreviousPage={hasPreviousPage}
        onPageChange={onPageChange}
        totalCount={totalCount}
        pageSize={25}
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

      {selectedInvoiceId && (
        <PaymentDialog
          open={isPaymentDialogOpen}
          onOpenChange={setIsPaymentDialogOpen}
          invoiceId={selectedInvoiceId}
          maxAmount={parseFloat(invoices.find(i => i.id === selectedInvoiceId)?.amount || '0') - (parseFloat(invoices.find(i => i.id === selectedInvoiceId)?.amount_paid || '0') || 0)}
          onPaymentAdded={() => {
            setIsPaymentDialogOpen(false)
            router.refresh()
          }}
        />
      )}
    </div>
  )
} 