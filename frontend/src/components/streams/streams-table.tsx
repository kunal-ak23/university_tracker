"use client"

import { Stream } from "@/types/contract"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Edit, Trash2 } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { deleteStream } from "@/lib/api/streams"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"

interface StreamsTableProps {
  streams: Stream[]
  universityId: string
}

export function StreamsTable({ streams, universityId }: StreamsTableProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [streamToDelete, setStreamToDelete] = useState<string | null>(null)

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Description</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {streams.map((stream) => (
            <TableRow key={stream.id}>
              <TableCell className="font-medium">{stream.name}</TableCell>
              <TableCell>{stream.duration} {stream.duration_unit}</TableCell>
              <TableCell>{stream.description}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Link href={`/universities/${universityId}/streams/${stream.id}/edit`}>
                    <Button variant="ghost" size="icon">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={() => setStreamToDelete(stream.id.toString())}
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
        open={streamToDelete !== null}
        onOpenChange={(open) => !open && setStreamToDelete(null)}
        onConfirm={async () => {
          if (!streamToDelete) return

          try {
            await deleteStream(streamToDelete)
            toast({
              title: "Success",
              description: "Stream deleted successfully",
            })
            router.refresh()
          } catch (error) {
            const errorMessage = error instanceof Error 
              ? error.message 
              : "Cannot delete stream. It may be in use by contracts."
            
            toast({
              title: "Error",
              description: errorMessage,
              variant: "destructive",
            })
          } finally {
            setStreamToDelete(null)
          }
        }}
        title="Delete Stream"
        description="Are you sure you want to delete this stream? This action cannot be undone."
      />
    </>
  )
} 