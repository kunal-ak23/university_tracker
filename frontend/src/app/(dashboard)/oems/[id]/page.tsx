import { getOEM } from "@/service/api/oems"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ExternalLink, Plus } from "lucide-react"
import { OEMActions } from "@/components/oems/oem-actions"
import { Button } from "@/components/ui/button"
import { Suspense } from "react"
import { OEMProgramsList } from "./programs-list"

export default async function OEMPage({
  params,
}: Readonly<{
  params: Promise<{ id: string }>
}>) {
  const { id } = await params
  let oem

  try {
    oem = await getOEM(id)
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{oem.name}</h2>
        <OEMActions oemId={id} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Contact Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Email</dt>
              <dd>{oem.contact_email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Phone</dt>
              <dd>{oem.contact_phone}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Website</dt>
              <dd>
                <Link 
                  href={oem.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:underline"
                >
                  {oem.website}
                  <ExternalLink className="ml-1 h-4 w-4" />
                </Link>
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Additional Information</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Point of Contact</dt>
              <dd>{oem.poc?.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">POC Email</dt>
              <dd>{oem.poc?.email}</dd>
            </div>
            <div className="space-y-2">
              <dt className="font-medium">Address</dt>
              <dd className="text-right whitespace-pre-line">{oem.address}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">Programs</h3>
          <Link href={`/programs/new?provider=${oem.id}`}>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Program
            </Button>
          </Link>
        </div>
        <Suspense fallback={<div className="flex items-center justify-center h-24">Loading...</div>}>
          <OEMProgramsList oemId={parseInt(id)} />
        </Suspense>
      </div>
    </div>
  )
} 
