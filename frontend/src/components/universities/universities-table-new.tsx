"use client"

import { University } from "@/types/university"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Edit, ExternalLink, Trash2, Layers, Eye } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { deleteUniversity } from "@/lib/api/universities"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface UniversitiesTableProps {
  universities: University[]
}

export function UniversitiesTable({ universities }: UniversitiesTableProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [universityToDelete, setUniversityToDelete] = useState<string | null>(null)

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Established Year</TableHead>
            <TableHead>Contact Email</TableHead>
            <TableHead>Contact Phone</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {universities.map((university) => (
            <TableRow key={university.id}>
              <TableCell>
                <Link 
                  href={`/universities/${university.id}`}
                  className="font-medium hover:underline cursor-pointer"
                >
                  {university.name}
                </Link>
              </TableCell>
              <TableCell>{university.established_year}</TableCell>
              <TableCell>{university.contact_email}</TableCell>
              <TableCell>{university.contact_phone}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link href={university.website} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="icon">
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Visit Website</p>
                      </TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link href={`/universities/${university.id}`}>
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>View Details</p>
                      </TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link href={`/universities/${university.id}/streams`}>
                          <Button variant="ghost" size="icon">
                            <Layers className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Manage Streams</p>
                      </TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link href={`/universities/${university.id}/edit`}>
                          <Button variant="ghost" size="icon">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Edit University</p>
                      </TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => setUniversityToDelete(university.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Delete University</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <ConfirmationDialog
        open={universityToDelete !== null}
        onOpenChange={(open) => !open && setUniversityToDelete(null)}
        onConfirm={async () => {
          if (!universityToDelete) return

          try {
            await deleteUniversity(universityToDelete)
            toast({
              title: "Success",
              description: "University deleted successfully",
            })
            router.refresh()
          } catch (error) {
            const errorMessage = error instanceof Error 
              ? error.message 
              : "Cannot delete university. It may have associated contracts or streams. Please remove those first."
            
            toast({
              title: "Error",
              description: errorMessage,
              variant: "destructive",
            })
          } finally {
            setUniversityToDelete(null)
          }
        }}
        title="Delete University"
        description="Are you sure you want to delete this university? This action cannot be undone. Any associated contracts or streams must be deleted first."
      />
    </>
  )
} 