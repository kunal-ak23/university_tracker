"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { useState } from "react"
import { MultiSelect } from "@/components/ui/multi-select"
import { Textarea } from "@/components/ui/textarea"
import { Billing } from "@/types/billing"
import { createBilling, updateBilling } from "@/service/api/billings"
import { Batch } from "@/types/batch"
import { Badge } from "@/components/ui/badge"
import { Users, Calendar, IndianRupee } from "lucide-react"

const billingFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  batches: z.array(z.string()).min(1, "At least one batch is required"),
  notes: z.string().optional(),
})

type BillingFormValues = z.infer<typeof billingFormSchema>

interface BillingFormProps {
  mode?: 'create' | 'edit'
  billing?: Billing
  availableBatches: Array<Batch>
}

function isBatch(batch: any): batch is Batch {
  return typeof batch === 'object' && batch !== null && 'id' in batch
}

export function BillingForm({ mode = 'create', billing, availableBatches }: BillingFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [selectedBatches, setSelectedBatches] = useState<string[]>(
    billing?.batches.map(b => {
      if (typeof b === 'number') return b.toString()
      if (typeof b === 'string') return b
      if (isBatch(b)) return b.id.toString()
      return ''
    }).filter(Boolean) || []
  )

  const form = useForm<BillingFormValues>({
    resolver: zodResolver(billingFormSchema),
    defaultValues: {
      name: billing?.name ?? "",
      notes: billing?.notes ?? "",
      batches: selectedBatches,
    },
  })

  // Get selected batch details
  const selectedBatchDetails = availableBatches.filter(batch => 
    selectedBatches.includes(batch.id.toString())
  )

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

  async function onSubmit(data: BillingFormValues) {
    try {
      if (mode === 'edit' && billing) {
        await updateBilling(billing.id, data)
        toast({
          title: "Success",
          description: "Billing updated successfully",
        })
      } else {
        await createBilling(data)
        toast({
          title: "Success",
          description: "Billing created successfully",
        })
      }
      router.push('/billings')
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} billing:`, error)
      toast({
        title: "Error",
        description: `Failed to ${mode} billing`,
        variant: "destructive",
      })
    }
  }

  // Calculate billing summary
  const billingSummary = selectedBatchDetails.reduce((summary, batch) => {
    const batchTotal = batch.number_of_students * parseFloat(batch.effective_cost_per_student)
    return {
      totalStudents: summary.totalStudents + batch.number_of_students,
      totalAmount: summary.totalAmount + batchTotal,
      totalOEMTransfer: summary.totalOEMTransfer + (batch.number_of_students * parseFloat(batch.oem_transfer_price || '0')),
    }
  }, {
    totalStudents: 0,
    totalAmount: 0,
    totalOEMTransfer: 0,
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Billing Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter billing name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="batches"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Batches</FormLabel>
              <FormControl>
                <MultiSelect
                  options={availableBatches.map(batch => ({
                    label: batch.name,
                    value: batch.id.toString()
                  }))}
                  value={field.value}
                  onValueChange={(values) => {
                    setSelectedBatches(values)
                    field.onChange(values)
                  }}
                  placeholder="Select batches"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Billing Summary */}
        {selectedBatchDetails.length > 0 && (
          <div className="rounded-lg border p-4 space-y-4">
            <h4 className="font-medium text-gray-700">Billing Summary</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-gray-500">Total Students</p>
                <p className="text-lg font-semibold">{billingSummary.totalStudents}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-gray-500">Total Amount</p>
                <p className="text-lg font-semibold">₹{billingSummary.totalAmount.toLocaleString('en-IN')}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-gray-500">OEM Transfer Amount</p>
                <p className="text-lg font-semibold">₹{billingSummary.totalOEMTransfer.toLocaleString('en-IN')}</p>
              </div>
            </div>
          </div>
        )}

        {/* Selected Batches Details */}
        {selectedBatchDetails.length > 0 && (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-700">Selected Batch Details</h4>
            <div className="grid grid-cols-2 gap-4">
              {selectedBatchDetails.map((batch) => (
                <div key={batch.id} className="rounded-lg border p-4 space-y-3">
                  <div className="flex justify-between items-start">
                    <h4 className="font-semibold">{batch.name}</h4>
                    <Badge className={getStatusColor(batch.status)}>
                      {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Users className="h-4 w-4" />
                      {batch.number_of_students} students
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="h-4 w-4" />
                      {batch.start_year} - {batch.end_year}
                    </div>
                    <div className="col-span-2 flex items-center gap-2 text-sm font-medium">
                      <IndianRupee className="h-4 w-4" />
                      Cost per Student: ₹{parseFloat(batch.effective_cost_per_student).toLocaleString('en-IN')}
                    </div>
                    <div className="col-span-2 flex items-center gap-2 text-sm font-medium">
                      <IndianRupee className="h-4 w-4" />
                      Batch Total: ₹{(batch.number_of_students * parseFloat(batch.effective_cost_per_student)).toLocaleString('en-IN')}
                    </div>
                  </div>
                  {batch.notes && (
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {batch.notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Add any additional notes..."
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
          >
            Cancel
          </Button>
          <Button type="submit">
            {mode === 'edit' ? 'Update' : 'Create'} Billing
          </Button>
        </div>
      </form>
    </Form>
  )
} 
