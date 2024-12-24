"use client"

import { getBatch } from "@/service/api/batches"
import { notFound } from "next/navigation"
import { BatchForm } from "@/components/batches/batch-form"

interface EditBatchPageProps {
  params: Promise<{
    id: string
    batchId: string
  }>
}

export default async function EditBatchPage({ params }: EditBatchPageProps) {
  const { id, batchId } = await params
  let batch
  
  try {
    batch = await getBatch(batchId)
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Edit Batch</h2>
      </div>
      <BatchForm mode="edit" batch={batch} streamId={id} />
    </div>
  )
} 
