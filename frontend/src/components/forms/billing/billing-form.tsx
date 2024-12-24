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

const billingFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  batches: z.array(z.string()).min(1, "At least one batch is required"),
  notes: z.string().optional(),
})

type BillingFormValues = z.infer<typeof billingFormSchema>

interface BillingFormProps {
  mode?: 'create' | 'edit'
  billing?: Billing
  availableBatches: Array<{ id: string; name: string }>
}

export function BillingForm({ mode = 'create', billing, availableBatches }: BillingFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [selectedBatches, setSelectedBatches] = useState<string[]>(
    billing?.batches.map(b => typeof b === 'string' ? b : b.id.toString()) || []
  )

  const form = useForm<BillingFormValues>({
    resolver: zodResolver(billingFormSchema),
    defaultValues: {
      name: billing?.name ?? "",
      notes: billing?.notes ?? "",
      batches: selectedBatches,
    },
  })

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
