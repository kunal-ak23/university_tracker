"use client"

import { StreamForm } from "@/components/streams/stream-form"


export default async function NewStreamPage({params}: {params: Promise<{
  id: string
}>}) {
  const {id} = await params;
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New Stream</h2>
      </div>
      <StreamForm universityId={id} />
    </div>
  )
} 