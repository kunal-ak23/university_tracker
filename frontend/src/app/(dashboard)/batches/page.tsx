"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { getBatches } from "@/lib/api/batches"
import { BatchesTable } from "@/components/batches/batches-table"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"
import { Batch } from "@/types/batch"

export default function BatchesPage() {
  const [batches, setBatches] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)
  const searchParams = useSearchParams()

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true)
        // Construct query string from search params
        const queryParams = new URLSearchParams()
        
        // Add search parameter if exists
        const search = searchParams.get('search')
        if (search) {
          queryParams.set('search', search)
        }

        // Add ordering parameter if exists
        const ordering = searchParams.get('ordering')
        if (ordering) {
          queryParams.set('ordering', ordering)
        }

        // Add page parameter if exists
        const page = searchParams.get('page')
        if (page) {
          queryParams.set('page', page)
        }

        const queryString = queryParams.toString()
        const url = queryString ? `/batches/?${queryString}` : '/batches/'
        
        const response = await getBatches(url)
        setBatches(response.results || response)
      } catch (error) {
        console.error('Failed to fetch batches:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBatches()
  }, [searchParams]) // Re-fetch when search params change

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Batches</h2>
        <Link href="/batches/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Batch
          </Button>
        </Link>
      </div>
      <BatchesTable batches={batches} />
    </div>
  )
} 