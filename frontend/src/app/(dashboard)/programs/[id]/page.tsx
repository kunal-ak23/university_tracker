import { getProgram } from "@/service/api/programs"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ExternalLink } from "lucide-react"
import { ProgramActions } from "./program-actions"

export default async function ProgramPage({
  params,
}: Readonly<{
  params: Promise<{ id: string }>
}>) {
  const { id } = await params
  let program

  try {
    program = await getProgram(parseInt(id))
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{program.name}</h2>
        <ProgramActions programId={program.id} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Program Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Program Code</dt>
              <dd>{program.program_code}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Duration</dt>
              <dd>{program.duration} {program.duration_unit}</dd>
            </div>
            <div className="space-y-2">
              <dt className="font-medium">Description</dt>
              <dd className="text-right whitespace-pre-line">{program.description || "No description provided"}</dd>
            </div>
            <div className="space-y-2">
              <dt className="font-medium">Prerequisites</dt>
              <dd className="text-right whitespace-pre-line">{program.prerequisites || "No prerequisites specified"}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Provider Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Name</dt>
              <dd>
                <Link href={`/oems/${program.provider.id}`} className="hover:underline">
                  {program.provider.name}
                </Link>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Website</dt>
              <dd>
                <Link 
                  href={program.provider.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:underline"
                >
                  {program.provider.website}
                  <ExternalLink className="ml-1 h-4 w-4" />
                </Link>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Contact Email</dt>
              <dd>{program.provider.contact_email}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
} 
