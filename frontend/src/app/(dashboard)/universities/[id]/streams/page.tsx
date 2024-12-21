"use client"

import { useEffect, useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Plus, Users } from "lucide-react"
import { Stream } from "@/types/contract"
import { getStreamsByUniversity } from "@/lib/api/streams"
import Link from "next/link"


export default function StreamsPage(params: {
    id: string
  }) {
  const {id} = params;
  const { toast } = useToast()
  const [streams, setStreams] = useState<Stream[]>([])

  useEffect(() => {
    async function fetchStreams() {
      try {
        const fetchedStreams = await getStreamsByUniversity(Number(id))
        setStreams(fetchedStreams)
      } catch (error) {
        console.error('Failed to fetch streams:', error)
        toast({
          title: "Error",
          description: "Failed to load streams",
          variant: "destructive",
        })
      }
    }
    fetchStreams()
  }, [id, toast])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Streams</h2>
        <Link href={`/universities/${id}/streams/new`}>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Stream
          </Button>
        </Link>
      </div>
      <div className="grid gap-4">
        {streams.map((stream, index) => (
          <div key={"Stream" + index} className="rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold">{stream.name}</h3>
                <p className="text-sm text-gray-600">
                  Duration: {stream.duration} {stream.duration_unit}
                </p>
              </div>
              <div className="flex gap-4">
                <Link href={`/universities/${id}/streams/${stream.id}`}>
                  <Button variant="outline">View Details</Button>
                </Link>
                <Link href={`/streams/${stream.id}/batches`}>
                  <Button variant="outline">
                    <Users className="mr-2 h-4 w-4" />
                    Manage Batches
                  </Button>
                </Link>
                <Link href={`/universities/${id}/streams/${stream.id}/edit`}>
                  <Button variant="ghost">Edit Stream</Button>
                </Link>
              </div>
            </div>
            {stream.description && (
              <p className="mt-2 text-gray-600">{stream.description}</p>
            )}
          </div>
        ))}
        {streams.length === 0 && (
          <p className="text-center text-gray-600">
            No streams found. Click "Add Stream" to create one.
          </p>
        )}
      </div>
    </div>
  )
} 