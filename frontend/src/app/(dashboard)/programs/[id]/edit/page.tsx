import { getProgram } from "@/service/api/programs"
import { ProgramForm } from "@/components/forms/program/program-form"
import { notFound } from "next/navigation"

export default async function EditProgramPage({
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
        <h2 className="text-3xl font-bold tracking-tight">Edit Program</h2>
      </div>
      <ProgramForm mode="edit" program={program} />
    </div>
  )
} 
