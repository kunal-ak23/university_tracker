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
import { createBilling, updateBilling, publishBilling } from "@/service/api/billings"
import { Batch } from "@/types/batch"
import { Badge } from "@/components/ui/badge"
import { Users, Calendar, IndianRupee, Percent } from "lucide-react"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"

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
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPublishDialog, setShowPublishDialog] = useState(false)
  const [draftId, setDraftId] = useState<string | null>(billing?.id || null)
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

  // Calculate billing summary
  const billingSummary = selectedBatchDetails.reduce((summary, batch) => {
    const baseAmount = batch.number_of_students * parseFloat(batch.effective_cost_per_student)
    const taxRate = parseFloat(batch.effective_tax_rate)
    const totalAmount = baseAmount * (1 + taxRate / 100)

    const baseOEMTransfer = batch.number_of_students * parseFloat(batch.effective_oem_transfer_price)
    const totalOEMTransfer = baseOEMTransfer * (1 + taxRate / 100)

    return {
      totalStudents: summary.totalStudents + batch.number_of_students,
      totalAmount: summary.totalAmount + totalAmount,
      totalOEMTransfer: summary.totalOEMTransfer + totalOEMTransfer,
    }
  }, {
    totalStudents: 0,
    totalAmount: 0,
    totalOEMTransfer: 0,
  })

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
      setIsSubmitting(true)
      if (mode === 'edit' && billing) {
        console.log(data, billing.id);
        await updateBilling(billing.id, data)
        toast({
          title: "Success",
          description: "Billing updated successfully",
        })
        router.push('/billings')
      } else {
        // Create draft billing
        console.log(data);
        const response = await createBilling(data)
        setDraftId(response.id)
        toast({
          title: "Success",
          description: "Draft billing created successfully. You can now review and publish it.",
        })
        // Don't redirect yet, allow user to publish
      }
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} billing:`, error)
      toast({
        title: "Error",
        description: `Failed to ${mode} billing`,
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handlePublish() {
    if (!draftId) return

    try {
      setIsSubmitting(true)
      await publishBilling(draftId)
      toast({
        title: "Success",
        description: "Billing published successfully",
      })
      router.push('/billings')
      router.refresh()
    } catch (error) {
      console.error('Failed to publish billing:', error)
      toast({
        title: "Error",
        description: "Failed to publish billing",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
      setShowPublishDialog(false)
    }
  }

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
              {selectedBatchDetails.map((batch) => {
                const effectiveCostPerStudent = parseFloat(batch.effective_cost_per_student)
                const effectiveOEMTransfer = parseFloat(batch.effective_oem_transfer_price)
                const effectiveTaxRate = parseFloat(batch.effective_tax_rate)
                const numStudents = batch.number_of_students

                const baseTotal = numStudents * effectiveCostPerStudent
                const taxAmount = baseTotal * (effectiveTaxRate / 100)
                const totalWithTax = baseTotal * (1 + effectiveTaxRate / 100)

                const baseOEMTransfer = numStudents * effectiveOEMTransfer
                const oemTaxAmount = baseOEMTransfer * (effectiveTaxRate / 100)
                const oemTotalWithTax = baseOEMTransfer * (1 + effectiveTaxRate / 100)

                return (
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
                        {numStudents} students
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="h-4 w-4" />
                        {batch.start_year} - {batch.end_year}
                      </div>
                      <div className="col-span-2 flex items-center gap-2 text-sm text-gray-600">
                        <Percent className="h-4 w-4" />
                        Tax Rate: {effectiveTaxRate}%
                      </div>
                      <div className="col-span-2 flex items-center gap-2 text-sm font-medium">
                        <IndianRupee className="h-4 w-4" />
                        Base Cost: ₹{effectiveCostPerStudent.toLocaleString('en-IN')} per student
                      </div>
                      <div className="col-span-2 flex items-center gap-2 text-sm font-medium">
                        <IndianRupee className="h-4 w-4" />
                        With Tax: ₹{(effectiveCostPerStudent * (1 + effectiveTaxRate / 100)).toLocaleString('en-IN')} per student
                      </div>
                      <div className="col-span-2 border-t pt-2">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>Base Total:</span>
                            <span>₹{baseTotal.toLocaleString('en-IN')}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>Tax Amount:</span>
                            <span>₹{taxAmount.toLocaleString('en-IN')}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm font-medium">
                            <span>Total with Tax:</span>
                            <span>₹{totalWithTax.toLocaleString('en-IN')}</span>
                          </div>
                        </div>
                      </div>
                      <div className="col-span-2 border-t pt-2">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>Base OEM Transfer:</span>
                            <span>₹{baseOEMTransfer.toLocaleString('en-IN')}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>Tax Amount:</span>
                            <span>₹{oemTaxAmount.toLocaleString('en-IN')}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm font-medium">
                            <span>OEM Total with Tax:</span>
                            <span>₹{oemTotalWithTax.toLocaleString('en-IN')}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {batch.notes && (
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {batch.notes}
                      </p>
                    )}
                  </div>
                )
              })}
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
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          {draftId ? (
            <Button
              type="button"
              onClick={() => setShowPublishDialog(true)}
              disabled={isSubmitting}
            >
              Publish Billing
            </Button>
          ) : (
            <Button type="submit" disabled={isSubmitting}>
              {mode === 'edit' ? 'Update' : 'Save as Draft'}
            </Button>
          )}
        </div>
      </form>

      <ConfirmationDialog
        open={showPublishDialog}
        onOpenChange={setShowPublishDialog}
        title="Publish Billing"
        description="Are you sure you want to publish this billing? This action cannot be undone."
        confirmText="Publish"
        onConfirm={handlePublish}
      />
    </Form>
  )
} 
