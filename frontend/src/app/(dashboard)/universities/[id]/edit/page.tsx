import { getUniversity } from "@/lib/api/universities"
import { UniversityForm } from "@/components/forms/university/university-form"
import { notFound } from "next/navigation"

export default async function EditUniversityPage({
  params,
}: Readonly<{
  params: Promise<{ id: string }>
}>) {
  const { id } = await params
  let university

  try {
    university = await getUniversity(id)
  } catch (error) {
    console.error(error)
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Edit University</h2>
      </div>
      <UniversityForm mode="edit" university={university} />
    </div>
  )
} 