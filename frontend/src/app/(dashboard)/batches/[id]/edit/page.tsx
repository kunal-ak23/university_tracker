"use client"

import { useEffect, useState, use } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Batch } from "@/lib/api/batches"
import { getBatch } from "@/lib/api/batches"
import { BatchForm } from "@/components/batches/batch-form"

export default function EditBatchPage({
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
    async function fetchBatch() {
      try {
        setIsLoading(true)
        const fetchedBatch = await getBatch(Number(id))
        setBatch(fetchedBatch)
      } catch (error) {
        console.error('Failed to fetch batch:', error)
        toast({
          title: "Error",
          description: "Failed to load batch",
          variant: "destructive",
        })
        router.push('/batches')
      } finally {
        setIsLoading(false)
      }
    }
    fetchBatch()
  }, [id, router, toast])

  if (isLoading || !batch) {
    return <div className="flex items-center justify-center h-24">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Edit Batch</h2>
        <p className="text-gray-600">Update batch details and settings.</p>
      </div>
      <BatchForm mode="edit" batch={batch} />
    </div>
  )
} 