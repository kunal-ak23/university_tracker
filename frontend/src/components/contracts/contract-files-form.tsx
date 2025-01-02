"use client"

import { Contract } from "@/types/contract"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/ui/file-upload"
import { useToast } from "@/hooks/use-toast"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"

interface ContractFilesFormProps {
  contract: Contract
  action: {
    upload: (formData: FormData) => Promise<void>
    delete: (fileId: number) => Promise<void>
  }
}

export function ContractFilesForm({ contract, action }: ContractFilesFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [files, setFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [fileToDelete, setFileToDelete] = useState<number | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    try {
      // Upload each file individually
      for (const file of files) {
        const formData = new FormData()
        
        // Add the file
        formData.append('file', file)
        formData.append('contract', contract.id.toString())
        formData.append('file_type', 'Contract File')
        formData.append('description', file.name)

        await action.upload(formData)
      }
      
      toast({
        title: "Upload Successful",
        description: "Contract files uploaded successfully",
        variant: "default",
      })
      
      router.push(`/contracts/${contract.id}`)
      router.refresh()
    } catch (error) {
      console.error('Failed to upload files:', error)
      toast({
        title: "Error",
        description: "Failed to upload contract files",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFileDelete = (fileId: number) => {
    setFileToDelete(fileId)
  }

  const confirmDelete = async () => {
    if (!fileToDelete) {
      return
    }

    try {
      await action.delete(fileToDelete)
      
      toast({
        title: "Delete successful",
        description: "File deleted successfully",
        variant: "default",
      })
      
      setFileToDelete(null)
      router.refresh()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete file",
        variant: "destructive",
      })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <FileUpload
        onFilesSelected={setFiles}
        existingFiles={contract.contract_files}
        onFileRemove={handleFileDelete}
      />

      <div className="flex justify-end gap-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
        >
          Cancel
        </Button>
        <Button 
          type="submit"
          disabled={files.length === 0 || isSubmitting}
        >
          {isSubmitting ? "Uploading..." : "Upload Files"}
        </Button>
      </div>

      <ConfirmationDialog
        open={fileToDelete !== null}
        onOpenChange={(open) => {
          if (!open) {
            setFileToDelete(null)
          }
        }}
        onConfirm={() => {
          confirmDelete()
        }}
        title="Delete File"
        description="Are you sure you want to delete this file? This action cannot be undone."
      />
    </form>
  )
} 