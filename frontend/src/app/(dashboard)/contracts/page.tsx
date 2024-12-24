"use client"

import { useEffect, useState } from "react"
import { ContractsTable } from "@/components/contracts/contracts-table"
import { Button } from "@/components/ui/button"
import { getContracts } from "@/service/api/contracts"
import { Plus } from "lucide-react"
import Link from "next/link"
import { Contract } from "@/types/contract"
import { useToast } from "@/hooks/use-toast"

export default function ContractsPage() {
  const { toast } = useToast()
  const [contracts, setContracts] = useState<Contract[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortColumn, setSortColumn] = useState<string>()
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>()

  const fetchContracts = async (
    page: number, 
    search?: string,
    ordering?: string
  ) => {
    try {
      setIsLoading(true)
      const response = await getContracts({ 
        page, 
        search,
        ordering,
        page_size: 25
      })
      setContracts(response.results)
      setTotalPages(Math.ceil(response.count / 25))
    } catch (error) {
      console.error('Failed to fetch contracts:', error)
      toast({
        title: "Error",
        description: "Failed to load contracts",
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
    fetchContracts(currentPage, searchQuery, ordering)
  }, [currentPage, searchQuery, sortColumn, sortDirection])

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

  if (isLoading && contracts.length === 0) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Contracts</h2>
        <Link href="/contracts/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Contract
          </Button>
        </Link>
      </div>
      <ContractsTable 
        contracts={contracts}
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        onSearch={handleSearch}
        onSort={handleSort}
        sortColumn={sortColumn}
        sortDirection={sortDirection}
      />
    </div>
  )
} 
