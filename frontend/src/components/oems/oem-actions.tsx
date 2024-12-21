"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { deleteOEM } from "@/lib/api/oems"
import Link from "next/link"
import { Edit, Trash2 } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface OEMActionsProps {
  oemId: string
}

export function OEMActions({ oemId }: OEMActionsProps) {
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
            <p>Delete OEM</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Link href={`/oems/${oemId}/edit`}>
              <Button 
                variant="default"
                size="icon"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent>
            <p>Edit OEM</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <ConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={async () => {
          try {
            await deleteOEM(oemId)
            toast({
              title: "Success",
              description: "OEM deleted successfully",
            })
            router.push('/oems')
            router.refresh()
          } catch (error) {
            const errorMessage = error instanceof Error 
              ? error.message 
              : "Cannot delete OEM. It may have associated contracts or programs. Please remove those first."
            
            toast({
              title: "Error",
              description: errorMessage,
              variant: "destructive",
            })
          }
        }}
        title="Delete OEM"
        description="Are you sure you want to delete this OEM? This action cannot be undone. Any associated contracts or programs must be deleted first."
      />
    </div>
  )
} 