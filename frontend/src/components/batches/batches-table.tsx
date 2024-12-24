"use client"

import { useToast } from "@/hooks/use-toast"
import { DataTable } from "@/components/ui/data-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Edit, Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { formatDate } from "@/lib/utils"
import { Batch } from "@/types/batch"
import { ColumnDef, Row } from "@tanstack/react-table"

interface BatchesTableProps {
  batches: Batch[]
  streamId?: string
  currentPage?: number
  totalPages?: number
  onPageChange?: (page: number) => void
  onSearch?: (query: string) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  hasNextPage?: boolean
  hasPreviousPage?: boolean
}

export function BatchesTable({ 
  batches,
  totalPages,
  hasNextPage,
  hasPreviousPage,
}: BatchesTableProps) {
  const { toast } = useToast()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ongoing':
        return 'bg-green-100 text-green-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      case 'planned':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const columns: ColumnDef<Batch, any>[] = [
    {
      id: "name",
      header: "Name",
      accessorFn: (row: Batch) => row.name,
      cell: ({ row }: { row: Row<Batch> }) => (
        <Link href={`/batches/${row.original.id}`} className="hover:underline">
          {row.original.name}
        </Link>
      ),
    },
    {
      id: "start_date",
      header: "Start Date",
      accessorFn: (row: Batch) => row.start_date,
      cell: ({ row }: { row: Row<Batch> }) => formatDate(row.original.start_date),
    },
    {
      id: "end_date",
      header: "End Date",
      accessorFn: (row: Batch) => row.end_date,
      cell: ({ row }: { row: Row<Batch> }) => formatDate(row.original.end_date),
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row: Batch) => row.status,
      cell: ({ row }: { row: Row<Batch> }) => (
        <Badge className={getStatusColor(row.original.status)}>
          {row.original.status.charAt(0).toUpperCase() + row.original.status.slice(1)}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }: { row: Row<Batch> }) => (
        <div className="flex items-center gap-2">
          <Link href={`/batches/${row.original.id}/edit`}>
            <Button variant="ghost" size="icon">
              <Edit className="h-4 w-4" />
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              toast({
                title: "Error",
                description: "Delete functionality is not implemented",
                variant: "destructive",
              })
            }}
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <DataTable<Batch, any>
      data={batches}
      columns={columns}
      pageCount={totalPages}
      searchPlaceholder="Search batches..."
      hasNextPage={hasNextPage}
      hasPreviousPage={hasPreviousPage}
    />
  )
} 