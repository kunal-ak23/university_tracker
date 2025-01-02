"use client"

import { useDebounce } from "@/hooks/use-debounce"
import { getBillings } from "@/service/api/billings"
import { Plus, Search } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { BillingList } from "@/components/billings/billing-list"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useRouter, usePathname, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { Billing } from "@/types/billing"
import { Input } from "@/components/ui/input"
import { PaginatedResponse } from "@/types/common"
import { 
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"


function getHeaderTitle(status: string) {
  switch (status) {
    case 'draft':
      return 'Draft Billings'
    case 'paid':
      return 'Paid Billings'
    case 'archived':
      return 'Archived Billings'
    case 'active':
    default:
      return 'Active Billings'
  }
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed p-8">
      <div className="text-center">
        <h3 className="mt-2 text-sm font-semibold text-gray-900">No billings</h3>
        <p className="mt-1 text-sm text-gray-500">Get started by creating a new billing.</p>
        <div className="mt-6">
          <Link href="/billings/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Billing
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-4 w-48 animate-pulse rounded bg-muted"></div>
              <div className="h-4 w-16 animate-pulse rounded bg-muted"></div>
            </div>
            <div className="flex items-center gap-6">
              <div className="h-8 w-24 animate-pulse rounded bg-muted"></div>
            </div>
          </div>
          <div className="mt-2">
            <div className="h-4 w-64 animate-pulse rounded bg-muted"></div>
          </div>
        </div>
      ))}
    </div>
  )
}

interface BillingTabsProps {
  defaultStatus: string
  initialBillings: Billing[]
}

export function BillingTabs({ defaultStatus, initialBillings }: BillingTabsProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const [activeStatus, setActiveStatus] = useState(defaultStatus || 'active')
  const [searchTerm, setSearchTerm] = useState("")
  const debouncedSearchTerm = useDebounce(searchTerm, 300)
  const [paginatedData, setPaginatedData] = useState<{ [key: string]: PaginatedResponse<Billing> }>({
    [defaultStatus || 'active']: {
      results: initialBillings,
      count: initialBillings.length,
      next: null,
      previous: null
    }
  })
  const [isLoading, setIsLoading] = useState<{ [key: string]: boolean }>({})
  const [currentPage, setCurrentPage] = useState<{ [key: string]: number }>({
    [defaultStatus || 'active']: 1
  })

  const fetchBillings = async (status: string, page = 1, search = "") => {
    if (isLoading[status]) return

    setIsLoading(prev => ({ ...prev, [status]: true }))
    try {
      const response = await getBillings({ 
        status, 
        page, 
        search: search.trim() // Trim the search term
      })
      setPaginatedData(prev => ({ ...prev, [status]: response }))
    } catch (error) {
      console.error('Error fetching billings:', error)
    } finally {
      setIsLoading(prev => ({ ...prev, [status]: false }))
    }
  }

  // Effect for handling tab changes and initial load
  useEffect(() => {
    if (activeStatus !== defaultStatus) {
      fetchBillings(activeStatus, 1)
    }
  }, [activeStatus, defaultStatus])

  // Separate effect for handling search
  useEffect(() => {
    // Only fetch if we have a search term or if we're clearing the search
    if (activeStatus) {
      fetchBillings(activeStatus, 1, debouncedSearchTerm)
    }
  }, [debouncedSearchTerm, activeStatus])

  const handleTabChange = (value: string) => {
    setActiveStatus(value)
    const params = new URLSearchParams(searchParams)
    params.set('status', value)
    router.push(`${pathname}?${params.toString()}`, { scroll: false })
  }

  const handlePageChange = (status: string, page: number) => {
    setCurrentPage(prev => ({ ...prev, [status]: page }))
    fetchBillings(status, page, debouncedSearchTerm)
  }

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchTerm(value)
    setCurrentPage({ [activeStatus]: 1 }) // Reset to first page on search
  }

  const renderPagination = (status: string) => {
    const data = paginatedData[status]
    if (!data || data.count <= 10) return null

    const totalPages = Math.ceil(data.count / 10)
    const currentPageNum = currentPage[status] || 1

    return (
      <Pagination className="mt-4">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious 
              onClick={() => handlePageChange(status, currentPageNum - 1)}
              disabled={currentPageNum === 1}
            />
          </PaginationItem>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <PaginationItem key={page}>
              <PaginationLink
                onClick={() => handlePageChange(status, page)}
                isActive={page === currentPageNum}
              >
                {page}
              </PaginationLink>
            </PaginationItem>
          ))}
          <PaginationItem>
            <PaginationNext
              onClick={() => handlePageChange(status, currentPageNum + 1)}
              disabled={currentPageNum === totalPages}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    )
  }

  const renderTabContent = (status: string) => {
    if (isLoading[status]) {
      return <LoadingState />
    }

    const data = paginatedData[status]
    if (!data || data.results.length === 0) {
      return <EmptyState />
    }

    return (
      <>
        <BillingList billings={data.results} />
        {renderPagination(status)}
      </>
    )
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search billings..."
          value={searchTerm}
          onChange={handleSearch}
          className="pl-8"
        />
      </div>

      <Tabs defaultValue={defaultStatus || 'active'} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="draft">Draft</TabsTrigger>
          <TabsTrigger value="paid">Paid</TabsTrigger>
          <TabsTrigger value="archived">Archived</TabsTrigger>
        </TabsList>
        <TabsContent value="active">
          {renderTabContent('active')}
        </TabsContent>
        <TabsContent value="draft">
          {renderTabContent('draft')}
        </TabsContent>
        <TabsContent value="paid">
          {renderTabContent('paid')}
        </TabsContent>
        <TabsContent value="archived">
          {renderTabContent('archived')}
        </TabsContent>
      </Tabs>
    </div>
  )
} 