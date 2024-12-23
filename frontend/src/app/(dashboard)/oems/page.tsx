"use client"

import { useEffect, useState } from "react"
import { deleteOEM, getOEMs } from "@/lib/api/oems"
import { OEMsTable } from "@/components/oems/oems-table"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"
import { OEM } from "@/types/oem"
import { useToast } from "@/hooks/use-toast"

export default function OEMsPage() {
  const { toast } = useToast()
  const [oems, setOEMs] = useState<OEM[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortColumn, setSortColumn] = useState<string>()
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>()

  const fetchOEMs = async (
    page: number, 
    search?: string,
    ordering?: string
  ) => {
    try {
      setIsLoading(true)
      const response = await getOEMs({ 
        page, 
        search,
        ordering,
        page_size: 25
      })
      setOEMs(response.results)
      setTotalCount(response.count)
      setTotalPages(Math.ceil(response.count / 25))
    } catch (error) {
      console.error('Failed to fetch OEMs:', error)
      toast({
        title: "Error",
        description: "Failed to load OEMs",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const ordering = sortColumn 
      ? `${sortDirection === 'desc' ? '-' : ''}${sortColumn}`
      : undefined
    fetchOEMs(currentPage, searchQuery, ordering)
  }, [currentPage, searchQuery, sortColumn, sortDirection, toast])

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setCurrentPage(1)
  }

  const handleSort = (column: string, direction: 'asc' | 'desc') => {
    setSortColumn(column)
    setSortDirection(direction)
    setCurrentPage(1)
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleDelete = async (id: string) => {
    setOEMs(oems.filter((oem) => oem.id !== id));
    fetchOEMs(currentPage, searchQuery, sortColumn)
  }

  if (isLoading && oems.length === 0) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">OEMs</h2>
        <Link href="/oems/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add OEM
          </Button>
        </Link>
      </div>
      <OEMsTable 
        oems={oems}
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        onSearch={handleSearch}
        onSort={handleSort}
        onDelete={handleDelete}
        sortColumn={sortColumn}
        sortDirection={sortDirection}
        hasNextPage={currentPage < totalPages}
        hasPreviousPage={currentPage > 1}
        totalCount={totalCount}
      />
    </div>
  )
} 