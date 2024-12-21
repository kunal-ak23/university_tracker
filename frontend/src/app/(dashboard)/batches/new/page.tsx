"use client"

import { BatchForm } from "@/components/batches/batch-form"

export default function NewBatchPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Create New Batch</h2>
        <p className="text-gray-600">Add a new batch to track students and revenue.</p>
      </div>
      <BatchForm mode="create" />
    </div>
  )
} 