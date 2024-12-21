import { getOEM } from "@/lib/api/oems"
import { OEMForm } from "@/components/forms/oem/oem-form"
import { notFound } from "next/navigation"

export default async function EditOEMPage({
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
        <h2 className="text-3xl font-bold tracking-tight">Edit OEM</h2>
      </div>
      <OEMForm mode="edit" oem={oem} />
    </div>
  )
} 