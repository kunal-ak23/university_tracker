import { getUniversity } from "@/lib/api/universities"
import { Stream } from "@/types/contract"
import { getStreamsByUniversity } from "@/lib/api/streams"
import { getBatchesByStream } from "@/lib/api/batches"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ExternalLink, Plus, Users, Calendar, IndianRupee, ClipboardList } from "lucide-react"
import { UniversityActions } from "@/components/universities/university-actions"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { University } from "@/types/university"


export default async function ViewUniversityPage(params:{
    id: string
  }) {
  const {id} = params;
  let university: University;
  let streams: Stream[];
  let allBatches = [];

  try {
    [university, streams] = await Promise.all([
      getUniversity(id),
      getStreamsByUniversity(Number(id))
    ])

    // Fetch batches for each stream
    const batchesPromises = streams.map(stream => getBatchesByStream(Number(stream.id)));
    const batchesResults = await Promise.all(batchesPromises)
    allBatches = batchesResults.flat().map(batch => ({
      ...batch,
      stream: streams.find(s => s.id === batch.stream)
    }))
  } catch (error) {
    console.error(error)
    notFound()
  }

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

  const totalStudents = allBatches.reduce((sum, batch) => sum + batch.number_of_students, 0)
  const ongoingBatches = allBatches.filter(batch => batch.status === 'ongoing')
  const totalRevenue = allBatches.reduce((sum, batch) => 
    sum + (parseFloat(batch.effective_cost_per_student) * batch.number_of_students), 0
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{university.name}</h2>
        <div className="flex gap-4">
          <Link href={`/universities/${id}/streams`}>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Manage Streams
            </Button>
          </Link>
          <UniversityActions universityId={id} />
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Users className="h-4 w-4" />
            <h4 className="font-medium">Total Students</h4>
          </div>
          <p className="text-2xl font-bold">{totalStudents}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <ClipboardList className="h-4 w-4" />
            <h4 className="font-medium">Active Batches</h4>
          </div>
          <p className="text-2xl font-bold">{ongoingBatches.length}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="h-4 w-4" />
            <h4 className="font-medium">Total Streams</h4>
          </div>
          <p className="text-2xl font-bold">{streams.length}</p>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-600">
            <IndianRupee className="h-4 w-4" />
            <h4 className="font-medium">Total Revenue</h4>
          </div>
          <p className="text-2xl font-bold">₹{totalRevenue.toLocaleString('en-IN')}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Contact Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Email</dt>
              <dd>{university.contact_email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Phone</dt>
              <dd>{university.contact_phone}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Website</dt>
              <dd>
                <Link 
                  href={university.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:underline"
                >
                  {university.website}
                  <ExternalLink className="ml-1 h-4 w-4" />
                </Link>
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Institution Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Established Year</dt>
              <dd>{university.established_year}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Accreditation</dt>
              <dd>{university.accreditation}</dd>
            </div>
          </dl>
        </div>

        <div className="col-span-2 rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Streams</h3>
            <Link href={`/universities/${id}/streams/new`}>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Stream
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {streams.map((stream) => (
              <div key={stream.id} className="rounded-lg border p-4 space-y-2">
                <h4 className="font-semibold">{stream.name}</h4>
                <p className="text-sm text-gray-600">
                  Duration: {stream.duration} {stream.duration_unit}
                </p>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {stream.description || "No description provided"}
                </p>
                <div className="flex justify-end">
                  <Link href={`/universities/${id}/streams/${stream.id}`}>
                    <Button variant="ghost" size="sm">View Details</Button>
                  </Link>
                </div>
              </div>
            ))}
            {streams.length === 0 && (
              <p className="col-span-3 text-center text-gray-600">
                No streams found. Click  &quot;Add Stream&quot; to create one.
              </p>
            )}
          </div>
        </div>

        <div className="col-span-2 rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">All Batches</h3>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {allBatches.map((batch) => (
              <div key={batch.id} className="rounded-lg border p-4 space-y-3">
                <div className="flex justify-between items-start">
                  <h4 className="font-semibold">{batch.name}</h4>
                  <Badge className={getStatusColor(batch.status)}>
                    {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600">
                  Stream: {batch.stream?.name}
                </p>
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
              </div>
            ))}
            {allBatches.length === 0 && (
              <p className="col-span-3 text-center text-gray-600">
                No batches found. Add streams and create batches to get started.
              </p>
            )}
          </div>
        </div>

        <div className="col-span-2 rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Address</h3>
          <p className="whitespace-pre-line">{university.address}</p>
        </div>
      </div>
    </div>
  )
} 