"use client"

import { BatchForm } from "@/components/batches/batch-form"
import { getBatchesByStream } from "@/lib/api/batches"
import { notFound } from "next/navigation"



export default async function EditBatchPage(params: {
    id: string
    batchId: string
  }) {
  const {id, batchId} = params;
  const batches = await getBatchesByStream(Number(id))
  const batch = batches.find(b => b.id.toString() === batchId)

  if (!batch) {
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Edit Batch</h2>
      </div>
      <BatchForm 
        mode="edit" 
        batch={batch} 
        streamId={id}
        contractId={batch.contract.toString()}
      />
    </div>
  )
} 