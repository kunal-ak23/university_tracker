"use client"

import { Button } from "@/components/ui/button"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { useToast } from "@/hooks/use-toast"
import { publishBilling, archiveBilling, deleteBilling } from "@/service/api/billings"
import { Billing } from "@/types/billing"
import { Archive, CheckCircle, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"

interface BillingActionsProps {
  billing: Billing
}

export function BillingActions({ billing }: BillingActionsProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [showPublishDialog, setShowPublishDialog] = useState(false)
  const [showArchiveDialog, setShowArchiveDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handlePublish = async () => {
    try {
      setIsLoading(true)
      await publishBilling(billing.id)
      toast({
        title: "Success",
        description: "Billing published successfully",
      })
      router.refresh()
    } catch (error) {
      console.error('Failed to publish billing:', error)
      toast({
        title: "Error",
        description: "Failed to publish billing",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setShowPublishDialog(false)
    }
  }

  const handleArchive = async () => {
    try {
      setIsLoading(true)
      await archiveBilling(billing.id)
      toast({
        title: "Success",
        description: "Billing archived successfully",
      })
      router.refresh()
    } catch (error) {
      console.error('Failed to archive billing:', error)
      toast({
        title: "Error",
        description: "Failed to archive billing",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setShowArchiveDialog(false)
    }
  }

  const handleDelete = async () => {
    try {
      setIsLoading(true)
      await deleteBilling(billing.id)
      toast({
        title: "Success",
        description: "Billing deleted successfully",
      })
      router.push('/billings')
      router.refresh()
    } catch (error) {
      console.error('Failed to delete billing:', error)
      toast({
        title: "Error",
        description: "Failed to delete billing",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setShowDeleteDialog(false)
    }
  }

  return (
    <>
      {billing.status === 'draft' && (
        <>
          <Button
            variant="outline"
            onClick={() => setShowPublishDialog(true)}
            disabled={isLoading}
          >
            <CheckCircle className="mr-2 h-4 w-4" />
            Publish
          </Button>
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
            disabled={isLoading}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </>
      )}

      {billing.status === 'active' && (
        <Button
          variant="outline"
          onClick={() => setShowArchiveDialog(true)}
          disabled={isLoading}
        >
          <Archive className="mr-2 h-4 w-4" />
          Archive
        </Button>
      )}

      <ConfirmationDialog
        open={showPublishDialog}
        onOpenChange={setShowPublishDialog}
        title="Publish Billing"
        description="Are you sure you want to publish this billing? This action cannot be undone. Once published, the billing will be marked as active."
        confirmText="Publish"
        onConfirm={handlePublish}
      />

      <ConfirmationDialog
        open={showArchiveDialog}
        onOpenChange={setShowArchiveDialog}
        title="Archive Billing"
        description="Are you sure you want to archive this billing? This will move it to the archived state and it will no longer be active."
        confirmText="Archive"
        onConfirm={handleArchive}
      />

      <ConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete Billing"
        description="Are you sure you want to delete this billing? This action cannot be undone and all associated data will be permanently removed."
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={handleDelete}
      />
    </>
  )
} 