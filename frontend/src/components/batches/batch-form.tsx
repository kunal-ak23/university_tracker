"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { createBatch, updateBatch } from "@/lib/api/batches"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useEffect, useState } from "react"
import { Contract } from "@/types/contract"
import { getContracts } from "@/lib/api/contracts"
import { TaxRate, getTaxRates } from "@/lib/api/tax"
import { cn } from "@/lib/utils"
import { Batch } from "@/types/batch"
import { Stream } from "@/types/stream"

const batchFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  stream: z.string().min(1, "Stream is required"),
  contract: z.string().min(1, "Contract is required"),
  number_of_students: z.string()
    .min(1, "Number of students is required"),
  start_year: z.string()
    .min(1, "Start year is required"),
  end_year: z.string()
    .min(1, "End year is required"),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().min(1, "End date is required"),
  cost_per_student_override: z.string().optional(),
  tax_rate_override: z.string().optional(),
  oem_transfer_price_override: z.string().optional(),
  status: z.enum(["planned", "ongoing", "completed"]),
  notes: z.string().optional(),
})

export type BatchFormValues = z.infer<typeof batchFormSchema>

interface BatchFormProps {
  mode?: 'create' | 'edit'
  batch?: Batch
  streamId?: string
  contractId?: string
}

const statusOptions = [
  { label: "Planned", value: "planned" },
  { label: "Ongoing", value: "ongoing" },
  { label: "Completed", value: "completed" },
]

export function BatchForm({ mode = 'create', batch }: BatchFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [streams, setStreams] = useState<Stream[]>([])
  const [contracts, setContracts] = useState<Contract[]>([])
  const [taxRates, setTaxRates] = useState<TaxRate[]>([])
  const [selectedContractDetails, setSelectedContractDetails] = useState<Contract | null>(null)
  const [initialValues, setInitialValues] = useState<BatchFormValues | null>(null)

  // Fetch contracts and tax rates on mount
  useEffect(() => {
    async function fetchData() {
      try {
        const [fetchedContracts, fetchedTaxRates] = await Promise.all([
          getContracts(),
          getTaxRates()
        ])
        setContracts(fetchedContracts.results)
        setTaxRates(fetchedTaxRates.results)
      } catch (error) {
        console.error('Failed to fetch data:', error)
        toast({
          title: "Error",
          description: "Failed to load required data",
          variant: "destructive",
        })
      }
    }
    fetchData()
  }, [toast])

  // Load initial streams if editing a batch
  useEffect(() => {
    if (mode === 'edit' && batch?.contract) {
      const contract = contracts.find(c => c.id.toString() === batch.contract.toString())
      console.log('contract', contract)
      if (contract) {
        setSelectedContractDetails(contract)
        setStreams(contract.streams)
      }
    }
  }, [mode, batch, contracts])

  console.log('taxRates', batch)
  const form = useForm<BatchFormValues>({
    resolver: zodResolver(batchFormSchema),
    defaultValues: {
      name: batch?.name ?? "",
      stream: batch?.stream?.toString() ?? "",
      contract: batch?.contract?.toString() ?? "",
      number_of_students: batch?.number_of_students?.toString() ?? "",
      start_year: batch?.start_year?.toString() ?? new Date().getFullYear().toString(),
      end_year: batch?.end_year?.toString() ?? (new Date().getFullYear() + 1).toString(),
      start_date: batch?.start_date ?? "",
      end_date: batch?.end_date ?? "",
      cost_per_student_override: batch?.cost_per_student_override ?? "",
      tax_rate_override: batch?.tax_rate_override !== undefined && batch?.tax_rate_override !== null 
        ? batch.tax_rate_override.toString() 
        : "none",
      oem_transfer_price_override: batch?.oem_transfer_price_override?.toString() ?? "",
      status: batch?.status ?? "planned",
      notes: batch?.notes ?? "",
    },
  })

  // Watch form state
  const formValues = form.watch()

  // Store initial values when form is mounted or batch changes
  useEffect(() => {
    const values = form.getValues()
    setInitialValues(values)
  }, [form, batch])

  // Function to check if form values have changed
  const hasFormChanged = () => {
    if (!initialValues) return false
    
    const changes = Object.keys(formValues).filter(key => {
      const initialValue = initialValues[key as keyof BatchFormValues]
      const currentValue = formValues[key as keyof BatchFormValues]
      
      // Handle special case for tax_rate_override
      if (key === 'tax_rate_override') {
        if (initialValue === 'none' && !currentValue) return false
        if (!initialValue && currentValue === 'none') return false
      }
      
      return initialValue !== currentValue
    })
    
    return changes.length > 0
  }

  // Update selected contract details when contract changes
  useEffect(() => {
    const subscription = form.watch(async (value, { name }) => {
      if (name === 'contract' && value.contract) {
        try {
          const selectedContract = contracts.find(c => c.id.toString() === value.contract)
          if (selectedContract) {
            setSelectedContractDetails(selectedContract)
            setStreams(selectedContract.streams)
            // Reset stream when contract changes
            form.setValue('stream', '')
          }
        } catch (error) {
          console.error('Failed to update streams:', error)
          toast({
            title: "Error",
            description: "Failed to load streams for the selected contract",
            variant: "destructive",
          })
        }
      }
    })
    return () => subscription.unsubscribe()
  }, [form, toast, contracts])

  // Function to calculate and format price difference
  const getPriceDifference = (original: string | null, override: string | null) => {
    if (!original || !override) return null
    const diff = parseFloat(override) - parseFloat(original)
    if (diff === 0) return null
    return {
      value: Math.abs(diff).toFixed(2),
      increased: diff > 0
    }
  }

  // Watch override values for comparison
  const costPerStudentOverride = form.watch('cost_per_student_override')
  const oemTransferPriceOverride = form.watch('oem_transfer_price_override')

  // Calculate differences
  const costDiff = selectedContractDetails ? getPriceDifference(
    selectedContractDetails.cost_per_student, 
    costPerStudentOverride || null
  ) : null
  const oemPriceDiff = selectedContractDetails ? getPriceDifference(
    selectedContractDetails.oem_transfer_price, 
    oemTransferPriceOverride || null
  ) : null

  async function onSubmit(data: BatchFormValues) {
    try {
      const submitData = {
        name: data.name,
        stream: parseInt(data.stream),
        contract: parseInt(data.contract),
        number_of_students: parseInt(data.number_of_students),
        start_year: parseInt(data.start_year),
        end_year: parseInt(data.end_year),
        start_date: data.start_date,
        end_date: data.end_date,
        cost_per_student_override: data.cost_per_student_override || null,
        tax_rate_override: data.tax_rate_override === "none" || !data.tax_rate_override
          ? null 
          : parseFloat(data.tax_rate_override),
        oem_transfer_price_override: data.oem_transfer_price_override || null,
        status: data.status,
        notes: data.notes || null,
      }

      if (mode === 'edit' && batch) {
        await updateBatch(batch.id.toString(), submitData)
        toast({
          title: "Success",
          description: "Batch updated successfully",
        })
      } else {
        await createBatch(submitData)
        toast({
          title: "Success",
          description: "Batch created successfully",
        })
      }
      router.push('/batches')
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} batch:`, error)
      toast({
        title: "Error",
        description: `Failed to ${mode} batch`,
        variant: "destructive",
      })
    }
  }

  const selectedContract = form.watch('contract')

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter batch name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="contract"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contract</FormLabel>
                <Select 
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select contract" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {contracts.map((contract) => (
                      <SelectItem 
                        key={contract.id} 
                        value={contract.id.toString()}
                      >
                        {contract.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="stream"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Stream</FormLabel>
                <Select 
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                  disabled={!selectedContract}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder={selectedContract ? "Select stream" : "Select a contract first"} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {streams.map((stream) => (
                      <SelectItem 
                        key={stream.id} 
                        value={stream.id.toString()}
                      >
                        {stream.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="number_of_students"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Number of Students</FormLabel>
                <FormControl>
                  <Input 
                    type="number" 
                    placeholder="Enter number of students" 
                    min="1"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select 
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {statusOptions.map((status) => (
                      <SelectItem 
                        key={status.value} 
                        value={status.value}
                      >
                        {status.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="start_year"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Start Year</FormLabel>
                <FormControl>
                  <Input 
                    type="number" 
                    placeholder="Enter start year" 
                    min="1900"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="end_year"
            render={({ field }) => (
              <FormItem>
                <FormLabel>End Year</FormLabel>
                <FormControl>
                  <Input 
                    type="number" 
                    placeholder="Enter end year" 
                    min="1900"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="start_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Start Date</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="end_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>End Date</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="space-y-4">
            <h3 className="text-lg font-medium">Cost Overrides</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField
                control={form.control}
                name="cost_per_student_override"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cost per Student Override</FormLabel>
                    <FormControl>
                      <div className="space-y-2">
                        <Input 
                          type="text" 
                          placeholder="Override contract's cost per student for this batch" 
                          {...field}
                        />
                        {selectedContractDetails && (
                          <div className="text-sm text-muted-foreground">
                            Original: {selectedContractDetails.cost_per_student}
                            {costDiff && (
                              <span className={cn(
                                "ml-2",
                                costDiff.increased ? "text-green-600" : "text-red-600"
                              )}>
                                ({costDiff.increased ? '+' : '-'}{costDiff.value})
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="tax_rate_override"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tax Rate Override</FormLabel>
                    <FormControl>
                      <div className="space-y-2">
                        <Select 
                          onValueChange={field.onChange}
                          value={field.value || "none"}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select tax rate override" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">No override</SelectItem>
                            {taxRates.map((taxRate, key) => (
                              <SelectItem 
                                key={`tax-rate-${key}`} 
                                value={taxRate.id.toString()}
                              >
                                {taxRate.name} ({taxRate.rate}%)
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="oem_transfer_price_override"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>OEM Transfer Price Override</FormLabel>
                    <FormControl>
                      <div className="space-y-2">
                        <Input 
                          type="text" 
                          placeholder="Override contract's OEM transfer price for this batch" 
                          {...field}
                        />
                        {selectedContractDetails && (
                          <div className="text-sm text-muted-foreground">
                            Original: {selectedContractDetails.oem_transfer_price}
                            {oemPriceDiff && (
                              <span className={cn(
                                "ml-2",
                                oemPriceDiff.increased ? "text-green-600" : "text-red-600"
                              )}>
                                ({oemPriceDiff.increased ? '+' : '-'}{oemPriceDiff.value})
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>

          <FormField
            control={form.control}
            name="notes"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Notes</FormLabel>
                <FormControl>
                  <Textarea 
                    placeholder="Enter any additional notes" 
                    className="min-h-[100px]"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <Button 
          type="submit" 
          disabled={mode === 'create' ? !form.formState.isDirty || !form.formState.isValid : !hasFormChanged() || !form.formState.isValid}
        >
          {mode === 'edit' ? 'Update' : 'Create'} Batch
        </Button>
      </form>
    </Form>
  )
} 