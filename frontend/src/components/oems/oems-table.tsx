"use client"

import { OEM } from "@/types/oem"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Edit, ExternalLink, Trash2 } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { deleteOEM } from "@/lib/api/oems"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"

interface OEMsTableProps {
  oems: OEM[]
}

export function OEMsTable({ oems }: OEMsTableProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [oemToDelete, setOemToDelete] = useState<string | null>(null)

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Contact Email</TableHead>
            <TableHead>Contact Phone</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {oems.map((oem) => (
            <TableRow key={oem.id}>
              <TableCell className="font-medium">{oem.name}</TableCell>
              <TableCell>{oem.contact_email}</TableCell>
              <TableCell>{oem.contact_phone}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Link href={oem.website} target="_blank" rel="noopener noreferrer">
                    <Button variant="ghost" size="icon">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Link href={`/oems/${oem.id}/edit`}>
                    <Button variant="ghost" size="icon">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={() => setOemToDelete(oem.id)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <ConfirmationDialog
        open={oemToDelete !== null}
        onOpenChange={(open) => !open && setOemToDelete(null)}
        onConfirm={async () => {
          if (!oemToDelete) return

          try {
            await deleteOEM(oemToDelete)
            toast({
              title: "Success",
              description: "OEM deleted successfully",
            })
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
          } finally {
            setOemToDelete(null)
          }
        }}
        title="Delete OEM"
        description="Are you sure you want to delete this OEM? This action cannot be undone. Any associated contracts or programs must be deleted first."
      />
    </>
  )
} 