"use client"

import { StreamForm } from "@/components/streams/stream-form"
import { getStream, getStreamsByUniversity } from "@/service/api/streams"
import { notFound } from "next/navigation"


export default async function EditStreamPage({params}: {params: Promise<{
  id: string
  streamId: string
}>}) {
  const {id, streamId} = await params;

  const stream = await getStream(Number(streamId));

  

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
