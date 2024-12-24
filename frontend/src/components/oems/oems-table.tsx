"use client"

import { OEM } from "@/types/oem"
import { DataTable } from "@/components/ui/data-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Edit, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { deleteOEM } from "@/service/api/oems"
import { useToast } from "@/hooks/use-toast"
import { ColumnDef, Row } from "@tanstack/react-table"

interface OEMsTableProps {
  oems: OEM[]
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  onSearch: (query: string) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  onDelete: (id: string) => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  hasNextPage?: boolean
  hasPreviousPage?: boolean
  totalCount: number
}

export function OEMsTable({ 
  oems,
  currentPage,
  totalPages,
  onPageChange,
  onDelete,
  totalCount,
}: OEMsTableProps) {
  const router = useRouter()
  const { toast } = useToast()

  const handleDelete = async (id: string) => {
    try {
      await deleteOEM(id)
      //remove from table
      onDelete(id);
      toast({
        title: "Success",
        description: "OEM deleted successfully",
      })
      router.refresh()
    } catch (error) {
      console.error(error);
      toast({
        title: "Error",
        description: "Failed to delete OEM",
        variant: "destructive",
      })
    }
  }

  const columns: ColumnDef<OEM, any>[] = [
    {
      id: "name",
      header: "Name",
      accessorFn: (row: OEM) => row.name,
      cell: ({ row }: { row: Row<OEM> }) => (
        <Link href={`/oems/${row.original.id}`} className="hover:underline">
          {row.original.name}
        </Link>
      ),
    },
    {
      id: "website",
      header: "Website",
      accessorFn: (row: OEM) => row.website,
      cell: ({ row }: { row: Row<OEM> }) => (
        <a href={row.original.website} target="_blank" rel="noopener noreferrer" className="hover:underline">
          {row.original.website}
        </a>
      ),
    },
    {
      id: "contact_email",
      header: "Contact Email",
      accessorFn: (row: OEM) => row.contact_email,
      cell: ({ row }: { row: Row<OEM> }) => row.original.contact_email,
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }: { row: Row<OEM> }) => (
        <div className="flex items-center gap-2">
          <Link href={`/oems/${row.original.id}/edit`}>
            <Button variant="ghost" size="icon">
              <Edit className="h-4 w-4" />
            </Button>
          </Link>
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
    <DataTable<OEM, any>
      data={oems}
      columns={columns}
      pageCount={totalPages}
      currentPage={currentPage}
      searchPlaceholder="Search OEMs..."
      hasNextPage={currentPage < totalPages}
      hasPreviousPage={currentPage > 1}
      onPageChange={onPageChange}
      totalCount={totalCount}
      pageSize={25}
    />
  )
} 
