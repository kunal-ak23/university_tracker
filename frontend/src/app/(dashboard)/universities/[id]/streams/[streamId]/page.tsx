"use client"

import { useEffect, useState, use } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Plus, Users } from "lucide-react"
import { Stream } from "@/types/contract"
import { Batch } from "@/lib/api/batches"
import { getStreamsByUniversity } from "@/lib/api/streams"
import { getBatchesByStream } from "@/lib/api/batches"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"

export default function StreamDetailPage({
  params,
}: Readonly<{
  params: Promise<{ id: string; streamId: string }>
}>) {
  const { id, streamId } = use(params)
  const router = useRouter()
  const { toast } = useToast()
  const [stream, setStream] = useState<Stream | null>(null)
  const [batches, setBatches] = useState<Batch[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        const streams = await getStreamsByUniversity(Number(id))
        const currentStream = streams.find(s => s.id.toString() === streamId)
        
        if (!currentStream) {
          router.push(`/universities/${id}/streams`)
          return
        }
        setStream(currentStream)

        const fetchedBatches = await getBatchesByStream(Number(streamId))
        setBatches(fetchedBatches)
      } catch (error) {
        console.error('Failed to fetch stream data:', error)
        toast({
          title: "Error",
          description: "Failed to load stream data",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [id, streamId, router, toast])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ongoing':
        return 'bg-green-100 text-green-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      case 'planned':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading || !stream) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  const totalStudents = batches.reduce((sum, batch) => sum + batch.number_of_students, 0)
  const ongoingBatches = batches.filter(batch => batch.status === 'ongoing')
  const totalRevenue = batches.reduce((sum, batch) => 
    sum + (parseFloat(batch.effective_cost_per_student) * batch.number_of_students), 0
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{stream.name}</h2>
          <p className="text-gray-600">Duration: {stream.duration} {stream.duration_unit}</p>
        </div>
        <div className="flex gap-4">
          <Link href={`/streams/${stream.id}/batches/new`}>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Batch
            </Button>
          </Link>
          <Link href={`/universities/${id}/streams/${stream.id}/edit`}>
            <Button variant="outline">Edit Stream</Button>
          </Link>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Users className="h-4 w-4" />
            <h4 className="font-medium">Total Students</h4>
          </div>
          <p className="text-2xl font-bold">{totalStudents}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Users className="h-4 w-4" />
            <h4 className="font-medium">Active Batches</h4>
          </div>
          <p className="text-2xl font-bold">{ongoingBatches.length}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Users className="h-4 w-4" />
            <h4 className="font-medium">Total Revenue</h4>
          </div>
          <p className="text-2xl font-bold">₹{totalRevenue.toLocaleString('en-IN')}</p>
        </div>
      </div>

      {/* Stream Description */}
      {stream.description && (
        <div className="rounded-lg border p-6">
          <h3 className="text-xl font-semibold mb-2">Description</h3>
          <p className="text-gray-600">{stream.description}</p>
        </div>
      )}

      {/* Batches Section */}
      <div className="rounded-lg border p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">Batches</h3>
          <Link href={`/streams/${stream.id}/batches`}>
            <Button variant="outline">
              <Users className="mr-2 h-4 w-4" />
              Manage All Batches
            </Button>
          </Link>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {batches.map((batch) => (
            <div key={batch.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex justify-between items-start">
                <h4 className="font-semibold">{batch.name}</h4>
                <Badge className={getStatusColor(batch.status)}>
                  {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Users className="h-4 w-4" />
                <span>{batch.number_of_students} Students</span>
              </div>
              <div className="text-sm text-gray-600">
                Duration: {batch.start_year} - {batch.end_year}
              </div>
              <div className="text-sm font-medium">
                Cost per Student: ₹{parseFloat(batch.effective_cost_per_student).toLocaleString('en-IN')}
                {batch.cost_per_student_override && ' (Override)'}
              </div>
              {batch.tax_rate_override && (
                <div className="text-sm text-gray-600">
                  Tax Rate: {batch.tax_rate_override}% (Override)
                </div>
              )}
              {batch.notes && (
                <p className="text-sm text-gray-600 line-clamp-2">
                  {batch.notes}
                </p>
              )}
              <div className="flex justify-end">
                <Link href={`/streams/${stream.id}/batches/${batch.id}/edit`}>
                  <Button variant="ghost" size="sm">Edit Batch</Button>
                </Link>
              </div>
            </div>
          ))}
          {batches.length === 0 && (
            <p className="col-span-3 text-center text-gray-600">
              No batches found. Click "Add Batch" to create one.
            </p>
          )}
        </div>
      </div>
    </div>
  )
} 