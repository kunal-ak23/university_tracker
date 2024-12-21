"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { Batch } from "@/lib/api/batches"
import { getBatchesByStream } from "@/lib/api/batches"
import { BatchesTable } from "@/components/batches/batches-table"


export default function BatchesPage({ id }: {id: string}) {
    
  const router = useRouter()
  const { toast } = useToast()
  const [batches, setBatches] = useState<Batch[]>([])

  useEffect(() => {
    async function fetchBatches() {
      try {
        const fetchedBatches = (await getBatchesByStream(Number(id))).results
        setBatches(fetchedBatches)
      } catch (error) {
        console.error('Failed to fetch batches:', error)
        toast({
          title: "Error",
          description: "Failed to load batches",
          variant: "destructive",
        })
      }
    }
    fetchBatches()
  }, [id, toast])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Batches</h2>
        <Button onClick={() => router.push(`/streams/${id}/batches/new`)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Batch
        </Button>
      </div>
      <BatchesTable batches={batches} streamId={id} />
    </div>
  )
} 