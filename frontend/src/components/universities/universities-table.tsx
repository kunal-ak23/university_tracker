"use client"

import { useState } from "react"
import { University } from "@/types/university"
import { DataTable } from "@/components/ui/data-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Edit, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { deleteUniversity } from "@/lib/api/universities"
import { useToast } from "@/hooks/use-toast"

interface UniversitiesTableProps {
  universities: University[]
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  onSearch: (query: string) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
}

export function UniversitiesTable({ 
  universities,
  currentPage,
  totalPages,
  onPageChange,
  onSearch,
  onSort,
  sortColumn,
  sortDirection,
}: UniversitiesTableProps) {
  const router = useRouter()
  const { toast } = useToast()

  const handleDelete = async (id: string) => {
    try {
      await deleteUniversity(id)
      toast({
        title: "Success",
        description: "University deleted successfully",
      })
      router.refresh()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete university",
        variant: "destructive",
      })
    }
  }

  const columns = [
    {
      id: "name",
      header: "Name",
      sortable: true,
      cell: ({ original }: { original: University }) => (
        <Link href={`/universities/${original.id}`} className="hover:underline">
          {original.name}
        </Link>
      ),
    },
    {
      id: "location",
      header: "Location",
      sortable: true,
      cell: ({ original }: { original: University }) => original.location,
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ original }: { original: University }) => (
        <div className="flex items-center gap-2">
          <Link href={`/universities/${original.id}/edit`}>
            <Button variant="ghost" size="icon">
              <Edit className="h-4 w-4" />
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleDelete(original.id)}
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <DataTable
      data={universities}
      columns={columns}
      currentPage={currentPage}
      pageCount={totalPages}
      onPageChange={onPageChange}
      onSearch={onSearch}
      onSort={onSort}
      sortColumn={sortColumn}
      sortDirection={sortDirection}
      searchPlaceholder="Search universities..."
    />
  )
}