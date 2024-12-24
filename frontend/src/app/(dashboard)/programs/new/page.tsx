import { ProgramForm } from "@/components/forms/program/program-form"

export default function NewProgramPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New Program</h2>
      </div>
      <ProgramForm />
    </div>
  )
} 