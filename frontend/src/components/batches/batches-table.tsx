"use client"

import { Batch } from "@/lib/api/batches"
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
import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { deleteBatch } from "@/lib/api/batches"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { Badge } from "@/components/ui/badge"

interface BatchesTableProps {
  batches: Batch[]
  onBatchDeleted: () => void
}

export function BatchesTable({ batches, onBatchDeleted }: BatchesTableProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [localBatches, setLocalBatches] = useState<Batch[]>([])

  useEffect(() => {
    setLocalBatches(batches)
  }, [batches])

  const handleDelete = async (batchId: number) => {
    try {
      await deleteBatch(batchId.toString())
      setLocalBatches(prevBatches => prevBatches.filter(batch => batch.id !== batchId))
      onBatchDeleted()
      toast({
        title: "Success",
        description: "Batch deleted successfully",
      })
    } catch (error) {
      console.error('Failed to delete batch:', error)
      toast({
        title: "Error",
        description: "Failed to delete batch",
        variant: "destructive",
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ongoing':
        return 'bg-green-100 text-green-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      case 'planned':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Stream</TableHead>
            <TableHead>Students</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Cost/Student</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {localBatches.map((batch) => (
            <TableRow key={batch.id}>
              <TableCell className="font-medium">{batch.name}</TableCell>
              <TableCell>{batch.stream?.name}</TableCell>
              <TableCell>{batch.number_of_students}</TableCell>
              <TableCell>
                {batch.start_year} - {batch.end_year}
              </TableCell>
              <TableCell>
                ₹{parseFloat(batch.effective_cost_per_student).toLocaleString('en-IN')}
                {batch.cost_per_student_override && ' (Override)'}
              </TableCell>
              <TableCell>
                <Badge className={getStatusColor(batch.status)}>
                  {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Link href={`/batches/${batch.id}/edit`}>
                    <Button variant="ghost" size="icon">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={() => handleDelete(batch.id)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
} 