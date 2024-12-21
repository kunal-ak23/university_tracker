"use client"

import { useState } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface DataTableProps<T> {
  data: T[]
  columns: {
    id: string
    header: string
    cell: (row: { original: T }) => React.ReactNode
    sortable?: boolean
  }[]
  pageCount?: number
  currentPage?: number
  onPageChange?: (page: number) => void
  searchPlaceholder?: string
  onSearch?: (query: string) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
}

export function DataTable<T>({
  data,
  columns,
  pageCount = 1,
  currentPage = 1,
  onPageChange,
  searchPlaceholder = "Search...",
  onSearch,
  onSort,
  sortColumn,
  sortDirection,
}: DataTableProps<T>) {
  const [searchDebounce, setSearchDebounce] = useState<NodeJS.Timeout>()

  const handleSearch = (value: string) => {
    if (searchDebounce) clearTimeout(searchDebounce)
    setSearchDebounce(
      setTimeout(() => {
        onSearch?.(value)
      }, 300)
    )
  }

  const handleSort = (columnId: string) => {
    if (!onSort) return

    const newDirection = 
      sortColumn === columnId && sortDirection === 'asc' ? 'desc' : 'asc'
    onSort(columnId, newDirection)
  }

  const getSortIcon = (columnId: string) => {
    if (sortColumn !== columnId) return <ArrowUpDown className="h-4 w-4" />
    return sortDirection === 'asc' ? 
      <ArrowUp className="h-4 w-4" /> : 
      <ArrowDown className="h-4 w-4" />
  }

  return (
    <div className="space-y-4">
      {onSearch && (
        <div className="flex items-center justify-between">
          <Input
            placeholder={searchPlaceholder}
            className="max-w-sm"
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.id}>
                  <div className="flex items-center space-x-2">
                    <span>{column.header}</span>
                    {column.sortable && onSort && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => handleSort(column.id)}
                      >
                        {getSortIcon(column.id)}
                      </Button>
                    )}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results found.
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, i) => (
                <TableRow key={i}>
                  {columns.map((column) => (
                    <TableCell key={column.id}>
                      {column.cell({ original: row })}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {pageCount > 1 && (
        <div className="flex items-center justify-end space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange?.(1)}
            disabled={currentPage === 1}
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange?.(currentPage - 1)}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm">
            Page {currentPage} of {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange?.(currentPage + 1)}
            disabled={currentPage === pageCount}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange?.(pageCount)}
            disabled={currentPage === pageCount}
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
} 