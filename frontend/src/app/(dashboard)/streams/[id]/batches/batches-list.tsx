"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { BatchesTable } from "@/components/batches/batches-table"
import { Batch } from "@/types/batch"

interface BatchesListProps {
  initialBatches: Batch[]
  streamId: string
}

export default function BatchesList({ initialBatches, streamId }: BatchesListProps) {
  const router = useRouter()
  const [batches] = useState<Batch[]>(initialBatches)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Batches</h2>
        <Button onClick={() => router.push(`/streams/${streamId}/batches/new`)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Batch
        </Button>
      </div>
      <BatchesTable batches={batches} streamId={streamId} />
    </div>
  )
} 