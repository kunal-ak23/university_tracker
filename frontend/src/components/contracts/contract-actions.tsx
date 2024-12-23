"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { deleteContract, updateContract } from "@/lib/api/contracts"
import Link from "next/link"
import { Archive, Edit, Trash2, CheckCircle } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface ContractActionsProps {
  contractId: string
  status: 'active' | 'planned' | 'inactive' | 'archived'
}

export function ContractActions({ contractId, status }: ContractActionsProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const handleStatusChange = async () => {
    try {
      const newStatus = status === 'archived' ? 'active' : 'archived'
      const formData = new FormData()
      formData.append('status', newStatus)
      
      await updateContract(contractId, formData)
      toast({
        title: "Success",
        description: `Contract ${newStatus === 'active' ? 'activated' : 'archived'} successfully`,
      })
      router.refresh()
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${status === 'archived' ? 'activate' : 'archive'} contract`,
        variant: "destructive",
      })
      console.error(error);
    }
  }

  return (
    <div className="flex gap-2">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button 
              variant={status === 'archived' ? "default" : "secondary"}
              size="icon"
              onClick={handleStatusChange}
            >
              {status === 'archived' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <Archive className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{status === 'archived' ? 'Make Active' : 'Archive Contract'}</p>
          </TooltipContent>
        </Tooltip>

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
            <p>Delete Contract</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Link href={`/contracts/${contractId}/edit`}>
              <Button 
                variant="default"
                size="icon"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent>
            <p>Edit Contract</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <ConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={async () => {
          try {
            await deleteContract(contractId)
            toast({
              title: "Success",
              description: "Contract deleted successfully",
            })
            router.push('/contracts')
            router.refresh()
          } catch (error) {
            toast({
              title: "Error",
              description: "Failed to delete contract",
              variant: "destructive",
            });
            console.error(error);
          }
        }}
        title="Delete Contract"
        description="Are you sure you want to delete this contract? This action cannot be undone."
      />
    </div>
  )
} 