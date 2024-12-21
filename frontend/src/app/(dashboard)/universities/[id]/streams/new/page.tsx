"use client"

import { StreamForm } from "@/components/streams/stream-form"


export default function NewStreamPage(params: {
    id: string
  }) {
  const {id} = params;
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New Stream</h2>
      </div>
      <StreamForm universityId={id} />
    </div>
  )
} 