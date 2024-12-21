"use client"

import { BatchForm } from "@/components/batches/batch-form"
import { useSearchParams } from "next/navigation"

interface NewBatchPageProps {
  params: {
    id: string
  }
}

export default function NewBatchPage(params: {id: string}) {
  const {id} = params;
  const searchParams = useSearchParams()
  const contractId = searchParams.get('contractId')

  if (!contractId) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold tracking-tight">Error</h2>
        </div>
        <p>Contract ID is required to create a batch.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New Batch</h2>
      </div>
      <BatchForm streamId={id} contractId={contractId} />
    </div>
  )
} 