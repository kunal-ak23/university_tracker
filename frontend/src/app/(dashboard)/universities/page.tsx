"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { University } from "@/types/university"
import { getUniversities } from "@/service/api/universities"
import { UniversitiesTable } from "@/components/universities/universities-table"

export default function UniversitiesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [universities, setUniversities] = useState<University[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortColumn, setSortColumn] = useState<string>()
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>()

  const fetchUniversities = async (
    page: number, 
    search?: string,
    ordering?: string
  ) => {
    try {
      setIsLoading(true)
      const response = await getUniversities({ 
        page, 
        search,
        ordering,
        page_size: 10
      })
      setUniversities(response.results)
      setTotalPages(Math.ceil(response.count / 10))
    } catch (error) {
      console.error('Failed to fetch universities:', error)
      toast({
        title: "Error",
        description: "Failed to load universities",
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
    fetchUniversities(currentPage, searchQuery, ordering);
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

  if (isLoading && universities.length === 0) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Universities</h2>
        <Button onClick={() => router.push('/universities/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Add University
        </Button>
      </div>
      <UniversitiesTable 
        universities={universities}
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
