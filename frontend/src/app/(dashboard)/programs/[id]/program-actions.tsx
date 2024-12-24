"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { deleteProgram } from "@/service/api/programs"
import Link from "next/link"
import { Edit, Trash2 } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface ProgramActionsProps {
  programId: number
}

export function ProgramActions({ programId }: ProgramActionsProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

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
            <p>Delete Program</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Link href={`/programs/${programId}/edit`}>
              <Button 
                variant="default"
                size="icon"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent>
            <p>Edit Program</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <ConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={async () => {
          try {
            await deleteProgram(programId)
            toast({
              title: "Success",
              description: "Program deleted successfully",
            })
            router.push('/programs')
            router.refresh()
          } catch (error) {
            const errorMessage = error instanceof Error 
              ? error.message 
              : "Cannot delete program. It may have associated contracts. Please remove those first."
            
            toast({
              title: "Error",
              description: errorMessage,
              variant: "destructive",
            })
          }
        }}
        title="Delete Program"
        description="Are you sure you want to delete this program? This action cannot be undone. Any associated contracts must be deleted first."
      />
    </div>
  )
} 
