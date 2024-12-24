"use client"

import { Contract } from "@/types/contract"
import { DataTable } from "@/components/ui/data-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Edit, Trash2, Archive } from "lucide-react"
import { useRouter } from "next/navigation"
import { archiveContract, deleteContract } from "@/service/api/contracts"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/components/ui/badge"
import { formatDate } from "@/service/utils"
import { ColumnDef, Row } from "@tanstack/react-table"

interface ContractsTableProps {
  contracts: Contract[]
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  onSearch: (query: string) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  hasNextPage?: boolean
  hasPreviousPage?: boolean
}

export function ContractsTable({ 
  contracts,
  currentPage,
  totalPages,
  onPageChange,
  onSearch,
  onSort,
  sortColumn,
  sortDirection,
  hasNextPage,
  hasPreviousPage,
}: ContractsTableProps) {
  const router = useRouter()
  const { toast } = useToast()

  const handleDelete = async (id: string) => {
    try {
      await deleteContract(id)
      toast({
        title: "Success",
        description: "Contract deleted successfully",
      })
      router.refresh()
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to delete contract",
        variant: "destructive",
      });
      console.error(err);
    }
  }

  const handleArchive = async (id: string) => {
    try {
      await archiveContract(id)
      toast({
        title: "Success",
        description: "Contract archived successfully",
      })
      router.refresh()
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to archive contract",
        variant: "destructive",
      })
      console.error(err);
    }
  }

  const columns: ColumnDef<Contract, any>[] = [
    {
      id: "name",
      header: "Name",
      accessorFn: (row: Contract) => row.name,
      cell: ({ row }: { row: Row<Contract> }) => (
        <Link href={`/contracts/${row.original.id}`} className="hover:underline">
          {row.original.name}
        </Link>
      ),
    },
    {
      id: "university",
      header: "University",
      accessorFn: (row: Contract) => row.university?.name,
      cell: ({ row }: { row: Row<Contract> }) => (
        <Link href={`/universities/${row.original.university?.id}`} className="hover:underline">
          {row.original.university?.name}
        </Link>
      ),
    },
    {
      id: "oem",
      header: "OEM",
      accessorFn: (row: Contract) => row.oem?.name,
      cell: ({ row }: { row: Row<Contract> }) => (
        <Link href={`/oems/${row.original.oem?.id}`} className="hover:underline">
          {row.original.oem?.name}
        </Link>
      ),
    },
    {
      id: "streams",
      header: "Streams",
      cell: ({ row }: { row: Row<Contract> }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.streams?.map((stream) => (
            <Badge key={stream.id} variant="outline">
              {stream.name}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      id: "programs",
      header: "Programs",
      cell: ({ row }: { row: Row<Contract> }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.programs?.map((program) => (
            <Badge key={program.id} variant="outline">
              {program.name}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      id: "cost_details",
      header: "Cost Details",
      cell: ({ row }: { row: Row<Contract> }) => (
        <div className="space-y-1 text-sm">
          <div>Cost/Student: ₹{row.original.cost_per_student}</div>
          <div>Transfer Price: ₹{row.original.oem_transfer_price}</div>
          <div>Tax Rate: {row.original.tax_rate}%</div>
        </div>
      ),
    },
    {
      id: "dates",
      header: "Duration",
      cell: ({ row }: { row: Row<Contract> }) => (
        <div className="space-y-1 text-sm">
          <div>Start: {row.original.start_date ? formatDate(row.original.start_date) : "-"}</div>
          <div>End: {row.original.end_date ? formatDate(row.original.end_date) : "-"}</div>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row: Contract) => row.status,
      cell: ({ row }: { row: Row<Contract> }) => (
        <Badge variant={row.original.status === 'active' ? 'default' : 'secondary'}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      id: "files",
      header: "Files",
      cell: ({ row }: { row: Row<Contract> }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.contract_files?.map((file: { id: number; file: string; description: string }) => (
            <a 
              key={file.id}
              href={file.file}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline text-sm text-blue-600"
            >
              {file.description}
            </a>
          ))}
        </div>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }: { row: Row<Contract> }) => (
        <div className="flex items-center gap-2">
          <Link href={`/contracts/${row.original.id}/edit`}>
            <Button variant="ghost" size="icon">
              <Edit className="h-4 w-4" />
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleArchive(row.original.id)}
          >
            <Archive className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleDelete(row.original.id)}
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <DataTable<Contract, any>
      data={contracts}
      columns={columns}
      pageCount={totalPages}
      searchPlaceholder="Search contracts..."
      hasNextPage={hasNextPage}
      hasPreviousPage={hasPreviousPage}
    />
  )
} 
