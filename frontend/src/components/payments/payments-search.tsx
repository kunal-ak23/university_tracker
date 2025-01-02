"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { useDebounce } from "@/hooks/use-debounce"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { 
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

interface PaymentsSearchProps {
  initialSearch: string
  initialPage: number
  totalPages: number
  totalCount: number
}

export function PaymentsSearch({ 
  initialSearch, 
  initialPage, 
  totalPages,
  totalCount 
}: PaymentsSearchProps) {
  const router = useRouter()
  const [search, setSearch] = useState(initialSearch)
  const [page, setPage] = useState(initialPage)
  const debouncedSearch = useDebounce(search, 300)

  useEffect(() => {
    const params = new URLSearchParams()
    if (debouncedSearch) params.set("search", debouncedSearch)
    if (page > 1) params.set("page", page.toString())
    
    const query = params.toString()
    router.push(`/payments${query ? `?${query}` : ""}`)
  }, [debouncedSearch, page, router])

  const handleSearch = (value: string) => {
    setSearch(value)
    setPage(1) // Reset to first page on search
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search payments..."
          className="pl-8"
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
        />
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {((page - 1) * 10) + 1}-{Math.min(page * 10, totalCount)} of {totalCount} payments
          </p>
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                />
              </PaginationItem>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                <PaginationItem key={pageNum}>
                  <PaginationLink
                    onClick={() => handlePageChange(pageNum)}
                    isActive={pageNum === page}
                  >
                    {pageNum}
                  </PaginationLink>
                </PaginationItem>
              ))}
              <PaginationItem>
                <PaginationNext
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === totalPages}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}
    </div>
  )
} 