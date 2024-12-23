"use client"

import { BatchForm } from "@/components/batches/batch-form"

interface NewBatchPageProps {
  params: Promise<{
    id: string
  }>
}

export default async function NewBatchPage({ params }: NewBatchPageProps) {
  const { id } = await params

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New Batch</h2>
      </div>
      <BatchForm mode="create" streamId={id} />
    </div>
  )
} 