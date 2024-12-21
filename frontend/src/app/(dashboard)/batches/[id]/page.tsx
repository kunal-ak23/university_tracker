"use client"

import { useEffect, useState, use } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Users, Calendar, IndianRupee } from "lucide-react"
import { Batch } from "@/lib/api/batches"
import { getBatch } from "@/lib/api/batches"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"

export default function BatchDetailPage({
  params,
}: Readonly<{
  params: Promise<{ id: string }>
}>) {
  const { id } = use(params)
  const router = useRouter()
  const { toast } = useToast()
  const [batch, setBatch] = useState<Batch | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        const fetchedBatch = await getBatch(Number(id))
        setBatch(fetchedBatch)
      } catch (error) {
        console.error('Failed to fetch batch data:', error)
        toast({
          title: "Error",
          description: "Failed to load batch data",
          variant: "destructive",
        })
        router.push('/batches')
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [id, router, toast])

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

  if (isLoading || !batch) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{batch.name}</h2>
          <p className="text-gray-600">Stream: {batch.stream?.name}</p>
        </div>
        <div className="flex gap-4">
          <Link href={`/batches/${batch.id}/edit`}>
            <Button>Edit Batch</Button>
          </Link>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Users className="h-4 w-4" />
            <h4 className="font-medium">Students</h4>
          </div>
          <p className="text-2xl font-bold">{batch.number_of_students}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="h-4 w-4" />
            <h4 className="font-medium">Duration</h4>
          </div>
          <p className="text-2xl font-bold">{batch.start_year} - {batch.end_year}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <IndianRupee className="h-4 w-4" />
            <h4 className="font-medium">Cost per Student</h4>
          </div>
          <p className="text-2xl font-bold">
            ₹{parseFloat(batch.effective_cost_per_student).toLocaleString('en-IN')}
            {batch.cost_per_student_override && ' (Override)'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Batch Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Status</dt>
              <dd>
                <Badge className={getStatusColor(batch.status)}>
                  {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                </Badge>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Start Date</dt>
              <dd>{new Date(batch.start_date).toLocaleDateString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">End Date</dt>
              <dd>{new Date(batch.end_date).toLocaleDateString()}</dd>
            </div>
            {batch.tax_rate_override && (
              <div className="flex justify-between">
                <dt className="font-medium">Tax Rate</dt>
                <dd>{batch.tax_rate_override}% (Override)</dd>
              </div>
            )}
          </dl>
        </div>

        {batch.notes && (
          <div className="rounded-lg border p-6 space-y-4">
            <h3 className="text-xl font-semibold">Notes</h3>
            <p className="whitespace-pre-line">{batch.notes}</p>
          </div>
        )}
      </div>
    </div>
  )
} 