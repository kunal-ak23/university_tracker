"use client"

import { useEffect, useState } from "react"
import { getInvoices } from "@/service/api/invoices"
import { InvoicesTable } from "@/components/invoices/invoices-table"
import { Invoice } from "@/types/payment"
import { useToast } from "@/hooks/use-toast"

export function InvoicesList() {
  const { toast } = useToast()
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortColumn, setSortColumn] = useState<string>()
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>()

  const fetchInvoices = async (
    page: number, 
    search?: string,
    ordering?: string
  ) => {
    try {
      setIsLoading(true)
      const response = await getInvoices({ 
        page, 
        search,
        ordering,
        page_size: 25
      })
      setInvoices(response.results)
      setTotalCount(response.count)
      setTotalPages(Math.ceil(response.count / 25))
    } catch (error) {
      console.error('Failed to fetch invoices:', error)
      toast({
        title: "Error",
        description: "Failed to load invoices",
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
    fetchInvoices(currentPage, searchQuery, ordering)
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
    setInvoices(invoices.filter((invoice) => invoice.id !== id))
    fetchInvoices(currentPage, searchQuery, sortColumn)
  }

  if (isLoading && invoices.length === 0) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <InvoicesTable 
      invoices={invoices}
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