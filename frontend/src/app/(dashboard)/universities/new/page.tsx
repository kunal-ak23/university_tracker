import { UniversityForm } from "@/components/forms/university/university-form"

export default function NewUniversityPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New University</h2>
      </div>
      <UniversityForm />
    </div>
  )
} 