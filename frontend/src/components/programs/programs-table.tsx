"use client"

import { Program } from "@/types/program"
import { DataTable } from "@/components/ui/data-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Edit, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { deleteProgram } from "@/service/api/programs"
import { useToast } from "@/hooks/use-toast"
import { ColumnDef, Row } from "@tanstack/react-table"

interface ProgramsTableProps {
  programs: Program[]
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
  showProvider?: boolean
}

export function ProgramsTable({ 
  programs,
  currentPage,
  totalPages,
  onPageChange,
  onSearch,
  onSort,
  sortColumn,
  sortDirection,
  onDelete,
  hasNextPage,
  hasPreviousPage,
  totalCount,
  showProvider = true,
}: ProgramsTableProps) {
  const router = useRouter()
  const { toast } = useToast()

  const handleDelete = async (id: number) => {
    try {
      await deleteProgram(id)
      onDelete(id)
      toast({
        title: "Success",
        description: "Program deleted successfully",
      })
      router.refresh()
    } catch (error) {
      console.error(error)
      toast({
        title: "Error",
        description: "Failed to delete program",
        variant: "destructive",
      })
    }
  }

  const columns: ColumnDef<Program, any>[] = [
    {
      id: "name",
      header: "Name",
      accessorFn: (row: Program) => row.name,
      cell: ({ row }: { row: Row<Program> }) => (
        <Link href={`/programs/${row.original.id}`} className="hover:underline">
          {row.original.name}
        </Link>
      ),
    },
    {
      id: "program_code",
      header: "Program Code",
      accessorFn: (row: Program) => row.program_code,
    },
    ...(showProvider ? [{
      id: "provider",
      header: "Provider",
      accessorFn: (row: Program) => row.provider?.name,
      cell: ({ row }: { row: Row<Program> }) => (
        <Link href={`/oems/${row.original.provider?.id}`} className="hover:underline">
          {row.original.provider?.name}
        </Link>
      ),
    }] : []),
    {
      id: "duration",
      header: "Duration",
      cell: ({ row }: { row: Row<Program> }) => (
        `${row.original.duration} ${row.original.duration_unit}`
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }: { row: Row<Program> }) => (
        <div className="flex items-center gap-2">
          <Link href={`/programs/${row.original.id}/edit`}>
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
    <DataTable<Program, any>
      data={programs}
      columns={columns}
      pageCount={totalPages}
      currentPage={currentPage}
      searchPlaceholder="Search programs..."
      hasNextPage={hasNextPage}
      hasPreviousPage={hasPreviousPage}
      onPageChange={onPageChange}
      totalCount={totalCount}
      pageSize={25}
    />
  )
} 
