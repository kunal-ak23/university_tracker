import { Suspense } from "react"
import { ProgramsList } from "./programs-list"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"

export default function ProgramsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Programs</h2>
        <Link href="/programs/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Program
          </Button>
        </Link>
      </div>
      <Suspense fallback={<div className="flex items-center justify-center h-24">Loading...</div>}>
        <ProgramsList />
      </Suspense>
    </div>
  )
} 