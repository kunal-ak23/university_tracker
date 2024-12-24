"use client"

import { useEffect, useState } from "react"
import { getPrograms } from "@/lib/api/programs"
import { ProgramsTable } from "@/components/programs/programs-table"
import { Program } from "@/types/program"
import { useToast } from "@/hooks/use-toast"

export function ProgramsList() {
  const { toast } = useToast()
  const [programs, setPrograms] = useState<Program[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortColumn, setSortColumn] = useState<string>()
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>()

  const fetchPrograms = async (
    page: number, 
    search?: string,
    ordering?: string
  ) => {
    try {
      setIsLoading(true)
      const response = await getPrograms({ 
        page, 
        search,
        ordering,
        page_size: 25
      })
      setPrograms(response.results)
      setTotalCount(response.count)
      setTotalPages(Math.ceil(response.count / 25))
    } catch (error) {
      console.error('Failed to fetch programs:', error)
      toast({
        title: "Error",
        description: "Failed to load programs",
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
    fetchPrograms(currentPage, searchQuery, ordering)
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

  const handleDelete = async (id: number) => {
    setPrograms(programs.filter((program) => program.id !== id));
    fetchPrograms(currentPage, searchQuery, sortColumn)
  }

  if (isLoading && programs.length === 0) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <ProgramsTable 
      programs={programs}
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
  )
} 