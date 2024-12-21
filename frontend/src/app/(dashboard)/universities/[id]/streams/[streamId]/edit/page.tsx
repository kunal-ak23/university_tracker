"use client"

import { StreamForm } from "@/components/streams/stream-form"
import { getStreamsByUniversity } from "@/lib/api/streams"
import { notFound } from "next/navigation"


export default async function EditStreamPage(params:  {
    id: string
    streamId: string
  }) {
  const {id, streamId} = params;
  const streams = await getStreamsByUniversity(Number(id))
  const stream = streams.find(s => s.id.toString() === streamId)

  if (!stream) {
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Edit Stream</h2>
      </div>
      <StreamForm 
        mode="edit" 
        stream={stream} 
        universityId={id}
      />
    </div>
  )
} 