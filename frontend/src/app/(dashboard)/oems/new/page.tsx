import { OEMForm } from "@/components/forms/oem/oem-form"

export default function NewOEMPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">New OEM</h2>
      </div>
      <OEMForm />
    </div>
  )
} 