"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { deleteUniversity } from "@/service/api/universities"
import Link from "next/link"
import { Edit, Trash2 } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface UniversityActionsProps {
  universityId: string
}

export function UniversityActions({ universityId }: UniversityActionsProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const handleDelete = async () => {
    try {
      await deleteUniversity(universityId)
      toast({
        title: "Success",
        description: "University deleted successfully",
      })
      router.push('/universities')
      router.refresh()
    } catch (error: unknown) {
      console.error('Failed to delete university:', error)
      toast({
        title: "Error",
        description: "Failed to delete university",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="flex gap-2">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button 
              variant="destructive"
              size="icon"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Delete University</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Link href={`/universities/${universityId}/edit`}>
              <Button 
                variant="default"
                size="icon"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent>
            <p>Edit University</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <ConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={handleDelete}
        title="Delete University"
        description="Are you sure you want to delete this university? This action cannot be undone."
      />
    </div>
  )
} 
