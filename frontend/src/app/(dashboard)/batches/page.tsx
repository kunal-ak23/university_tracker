"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { Batch } from "@/lib/api/batches"
import { getBatches } from "@/lib/api/batches"
import { BatchesTable } from "@/components/batches/batches-table"

export default function BatchesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [batches, setBatches] = useState<Batch[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchBatches = async () => {
    try {
      setIsLoading(true)
      const fetchedBatches = (await getBatches()).results
      setBatches(fetchedBatches)
    } catch (error) {
      console.error('Failed to fetch batches:', error)
      toast({
        title: "Error",
        description: "Failed to load batches",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchBatches()
  }, [toast])

  if (isLoading) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Batches</h2>
        <Button onClick={() => router.push('/batches/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Add Batch
        </Button>
      </div>
      <BatchesTable 
        batches={batches} 
        onBatchDeleted={fetchBatches}
      />
    </div>
  )
} 