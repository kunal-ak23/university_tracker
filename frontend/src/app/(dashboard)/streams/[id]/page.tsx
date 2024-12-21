import { getStreamsByUniversity } from "@/lib/api/streams"
import { getBatchesByStream } from "@/lib/api/batches"
import Link from "next/link"
import { notFound } from "next/navigation"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

interface StreamPageProps {
  params: {
    id: string
  }
}

export default async function StreamPage({ id }: {id: string}) {
  let stream
  let batches

  try {
    const streams = await getStreamsByUniversity(Number(id))
    stream = streams.find(s => s.id.toString() === id)
    if (!stream) {
      notFound()
    }

    batches = await getBatchesByStream(Number(id))
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{stream.name}</h2>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Stream Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Duration</dt>
              <dd>{stream.duration} {stream.duration_unit}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Description</dt>
              <dd>{stream.description || "No description provided"}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Batches</h3>
            <Link href={`/streams/${id}/batches`}>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Manage Batches
              </Button>
            </Link>
          </div>
          <div className="space-y-4">
            {batches.map((batch) => (
              <div key={batch.id} className="rounded-lg border p-4 space-y-2">
                <h4 className="font-semibold">{batch.name}</h4>
                <p className="text-sm text-gray-600">
                  Students: {batch.number_of_students}
                </p>
                <p className="text-sm text-gray-600">
                  Duration: {batch.start_year} - {batch.end_year}
                </p>
                <p className="text-sm text-gray-600">
                  Cost per Student: ₹{parseFloat(batch.effective_cost_per_student).toLocaleString('en-IN')}
                </p>
              </div>
            ))}
            {batches.length === 0 && (
              <p className="text-center text-gray-600">
                No batches found. Click "Manage Batches" to add some.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 