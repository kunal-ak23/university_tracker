"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { FileUpload } from "@/components/ui/file-upload"
import { useState, useEffect } from "react"
import { createContract, updateContract, deleteContract, archiveContract } from "@/service/api/contracts"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { MultiSelect } from "@/components/ui/multi-select"
import { getUniversities, getUniversityStreams } from "@/service/api/universities"
import { getOEMs, getOEMPrograms } from "@/service/api/oems"
import { getTaxRates, TaxRate } from "@/service/api/tax"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { Contract, Stream } from "@/types/contract"
import { University } from "@/types/university"
import { OEM } from "@/types/oem"

const contractFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  university: z.union([z.string(), z.number()]).transform(val => val.toString()),
  oem: z.union([z.string(), z.number()]).transform(val => val.toString()),
  cost_per_student: z.string().min(1, "Cost per student is required"),
  oem_transfer_price: z.string().min(1, "OEM transfer price is required"),
  tax_rate: z.string().min(1, "Tax rate is required"),
  status: z.enum(["active", "planned", "inactive", "archived"]),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().min(1, "End date is required"),
  programs: z.array(z.union([z.string(), z.number()])).transform(arr => arr.map(val => val.toString())),
  streams: z.array(z.union([z.string(), z.number()])).transform(arr => arr.map(val => val.toString())),
})

type ContractFormValues = z.infer<typeof contractFormSchema>

interface ContractFormProps {
  mode?: 'create' | 'edit'
  contract?: Contract
}

const statusOptions = [
  { label: "Active", value: "active" },
  { label: "Planned", value: "planned" },
  { label: "Inactive", value: "inactive" },
  { label: "Archived", value: "archived" },
] as const

export function ContractForm({ mode = 'create', contract }: ContractFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [files, setFiles] = useState<File[]>([])
  const [universities, setUniversities] = useState<University[]>([])
  const [oems, setOems] = useState<OEM[]>([])
  const [selectedPrograms, setSelectedPrograms] = useState<string[]>([])
  const [selectedStreams, setSelectedStreams] = useState<string[]>([])
  const [availablePrograms, setAvailablePrograms] = useState<Array<{ id: string; name: string }>>([])
  const [availableStreams, setAvailableStreams] = useState<Array<{ id: string; name: string }>>([])
  const [isDirty, setIsDirty] = useState(false)
  const [hasFileChanges, setHasFileChanges] = useState(false)
  const [taxRates, setTaxRates] = useState<TaxRate[]>([])
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  // Add console.log to debug the contract data
  useEffect(() => {
    if (mode === 'edit' && contract) {
      console.log('Contract Data:', contract)
      console.log('University ID:', contract.university?.id)
      console.log('OEM ID:', contract.oem?.id)
    }
  }, [mode, contract])

  const form = useForm<ContractFormValues>({
    resolver: zodResolver(contractFormSchema),
    mode: "all",
    reValidateMode: "onChange",
    defaultValues: {
      name: contract?.name ?? "",
      university: contract?.university?.id?.toString() ?? "",
      oem: contract?.oem?.id?.toString() ?? "",
      cost_per_student: contract?.cost_per_student?.toString() ?? "",
      oem_transfer_price: contract?.oem_transfer_price?.toString() ?? "",
      tax_rate: contract?.tax_rate?.toString() ?? "",
      status: contract?.status as "active" | "planned" | "inactive" | "archived" | undefined ?? "planned",
      start_date: contract?.start_date ?? "",
      end_date: contract?.end_date ?? "",
      programs: contract?.programs?.map(cp => cp.id.toString()) ?? [],
      streams: contract?.streams?.map(s => s.id.toString()) ?? [],
    },
  })

  // Fetch universities and OEMs on mount
  useEffect(() => {
    async function fetchData() {
      try {
        const [universitiesData, oemsData, taxRatesData] = await Promise.all([
          getUniversities(),
          getOEMs(),
          getTaxRates()
        ])
        
        setUniversities(universitiesData.results);
        setOems(oemsData.results);
        setTaxRates(taxRatesData.results)

        // Set default tax rate (rate 18)
        const defaultTaxRate = taxRates.find(tax => tax.rate === 18)
        if (defaultTaxRate && !contract) {  // Only set default for new contracts
          form.setValue('tax_rate', defaultTaxRate.id.toString())
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      }
    }
    fetchData()
  }, [form, contract])

  // Initialize selected values for edit mode
  useEffect(() => {
    async function initializeEditMode() {
      if (mode === 'edit' && contract) {
        try {
          setSelectedPrograms(contract.programs.map(cp => cp.id.toString()));
          setSelectedStreams(contract.streams.map(s => s.id.toString()))
          
          if (contract.oem?.id) {
            const programs = await getOEMPrograms(contract.oem.id.toString())
            setAvailablePrograms(programs.results)
          }
          
          if (contract.university?.id) {
            const streams = await getUniversityStreams(contract.university.id.toString())
            // @ts-ignore
            setAvailableStreams(streams.results)
          }
        } catch (error) {
          console.error('Failed to initialize edit mode:', error)
          toast({
            title: "Error",
            description: "Failed to load initial data",
            variant: "destructive",
          })
        }
      }
    }

    initializeEditMode()
  }, [mode, contract, toast, form])

  // Update available streams when university changes
  const onUniversityChange = async (universityId: string) => {
    try {
      const streams = await getUniversityStreams(universityId)
      // @ts-ignore
      setAvailableStreams(streams.results)
      setSelectedStreams([])
      form.setValue('streams', [])
    } catch (error) {
      console.error('Failed to fetch university streams:', error)
      toast({
        title: "Error",
        description: "Failed to load streams for selected university",
        variant: "destructive",
      })
    }
  }

  // Update available programs when OEM changes
  const onOEMChange = async (oemId: string) => {
    try {
      const programs = await getOEMPrograms(oemId)
      setAvailablePrograms(programs.results)
      setSelectedPrograms([])
      form.setValue('programs', [])
    } catch (error) {
      console.error('Failed to fetch OEM programs:', error)
      toast({
        title: "Error",
        description: "Failed to load programs for selected OEM",
        variant: "destructive",
      })
    }
  }

  // Update the file selection handler
  const handleFilesSelected = (newFiles: File[]) => {
    setFiles(newFiles)
    setHasFileChanges(true)
    setIsDirty(true)
  }

  // Track form changes
  useEffect(() => {
    if (mode === 'edit') {
      const subscription = form.watch((value) => {
        const hasFormChanged = Object.entries(value).some(([key, val]) => {
          if (key === 'programs') {
            const currentPrograms = val as string[]
            const originalPrograms = contract?.programs?.map(cp => cp.id.toString()) || []
            return !areArraysEqual(currentPrograms.sort(), originalPrograms.sort())
          }
          if (key === 'streams') {
            const currentStreams = val as string[]
            const originalStreams = contract?.streams?.map(s => s.id.toString()) || []
            return !areArraysEqual(currentStreams.sort(), originalStreams.sort())
          }
          if (key === 'cost_per_student' || key === 'oem_transfer_price') {
            return val?.toString() !== contract?.[key]?.toString()
          }
          // @ts-ignore
          return val !== contract?.[key]?.toString()
        })

        setIsDirty(hasFormChanged || hasFileChanges)
      })

      return () => subscription.unsubscribe()
    }
  }, [form, mode, contract, hasFileChanges])

  // Helper function to compare arrays
  const areArraysEqual = (arr1: string[], arr2: string[]) => {
    if (arr1.length !== arr2.length) return false
    return arr1.every((value, index) => value === arr2[index])
  }

  async function onSubmit(data: ContractFormValues) {
    try {
      if (files.length === 0 && mode === 'create') {
        toast({
          title: "Error",
          description: "Please upload at least one contract file",
          variant: "destructive",
        })
        return
      }

      const formData = new FormData()
      
      // Add contract data
      Object.entries(data).forEach(([key, value]) => {
        if (key === 'streams') {
            // Convert string IDs back to numbers for streams
            const numericIds = (value as string[]).map(id => parseInt(id))
            numericIds.forEach(id => {
                formData.append('streams_ids[]', id.toString())
            })
        } else if (key === 'programs') {
            // Convert string IDs back to numbers for programs
            const numericIds = (value as string[]).map(id => parseInt(id))
            // Ensure it's sent as an array even with single value
            numericIds.forEach(id => {
                formData.append('programs_ids[]', id.toString())
            })
        } else if (key === 'university' || key === 'oem') {
          // Convert string IDs back to numbers for single values
          formData.append(key, parseInt(value as string).toString())
        } else if (key === 'tax_rate') {
          formData.append(key, parseFloat(value as string).toString())
        } else {
          formData.append(key, value as string)
        }
      })

      // Add files only in create mode or if new files are added in edit mode
      if (files.length > 0) {
        files.forEach(file => {
          formData.append('files', file)
        })
      }

      let updatedContract
      if (mode === 'edit' && contract) {
        updatedContract = await updateContract(contract.id, formData)
      } else {
        updatedContract = await createContract(formData)
      }
      
      toast({
        title: "Success",
        description: `Contract ${mode === 'edit' ? 'updated' : 'created'} successfully`,
      })

      router.push(`/contracts/${updatedContract.id}`)
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} contract:`, error)
      
      // Handle server validation errors
      if (error instanceof Error) {
        try {
          const errorData = JSON.parse(error.message)
          
          // Set server-side validation errors in the form
          if (typeof errorData === 'object') {
            Object.keys(errorData).forEach((key) => {
              const messages = errorData[key]
              if (Array.isArray(messages)) {
                form.setError(key as keyof ContractFormValues, {
                  type: 'server',
                  message: messages.join(', ')
                })
              } else if (typeof messages === 'string') {
                form.setError(key as keyof ContractFormValues, {
                  type: 'server',
                  message: messages
                })
              }
            })
          }
          
          // Show a toast with the first error message
          const firstError = Object.values(errorData)[0]
          const errorMessage = Array.isArray(firstError) ? firstError[0] : firstError
          
          toast({
            title: "Error",
            description: errorMessage || `Failed to ${mode} contract`,
            variant: "destructive",
          })
        } catch {
          // If error message isn't JSON, show it directly
          toast({
            title: "Error",
            description: error.message || `Failed to ${mode} contract`,
            variant: "destructive",
          })
        }
      } else {
        toast({
          title: "Error",
          description: `Failed to ${mode} contract`,
          variant: "destructive",
        })
      }
    }
  }

  // Add delete handler
  const handleDelete = async () => {
    try {
      await deleteContract(contract!.id)
      toast({
        title: "Success",
        description: "Contract deleted successfully",
      })
      router.push('/contracts')
      router.refresh()
    } catch (error) {
      console.error('Failed to delete contract:', error)
      toast({
        title: "Error",
        description: "Failed to delete contract",
        variant: "destructive",
      })
    }
  }

  // Add archive handler
  const handleArchive = async () => {
    try {
      await archiveContract(contract!.id)
      toast({
        title: "Success",
        description: "Contract archived successfully",
      })
      router.refresh()
    } catch (error) {
      console.error('Failed to archive contract:', error)
      toast({
        title: "Error",
        description: "Failed to archive contract",
        variant: "destructive",
      })
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem className="col-span-2">
                <FormLabel>Contract Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter contract name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* OEM and Programs Group */}
          <div className="space-y-6">
            <FormField
              control={form.control}
              name="oem"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>OEM</FormLabel>
                  <Select 
                    onValueChange={(value) => {
                      field.onChange(value)
                      onOEMChange(value)
                    }}
                    value={field.value?.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an OEM" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {oems.map((oem) => (
                        <SelectItem key={oem.id} value={oem.id.toString()}>
                          {oem.name}
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
              name="programs"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Programs</FormLabel>
                  <FormControl>
                    <MultiSelect
                      disabled={!form.getValues("oem")}
                      placeholder={form.getValues("oem") ? "Select programs" : "Select an OEM first"}
                      options={availablePrograms.map(program => ({
                        label: program.name,
                        value: program.id.toString()
                      }))}
                      value={field.value}
                      onValueChange={(values) => {
                        setSelectedPrograms(values)
                        field.onChange(values)
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {/* University and Streams Group */}
          <div className="space-y-6">
            <FormField
              control={form.control}
              name="university"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>University</FormLabel>
                  <Select 
                    onValueChange={(value) => {
                      field.onChange(value)
                      onUniversityChange(value)
                    }}
                    value={field.value?.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a university" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {universities.map((university) => (
                        <SelectItem 
                          key={university.id} 
                          value={university.id.toString()}
                        >
                          {university.name}
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
              name="streams"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Streams</FormLabel>
                  <FormControl>
                    <MultiSelect
                      disabled={!form.getValues("university")}
                      placeholder={form.getValues("university") ? "Select streams" : "Select a university first"}
                      options={availableStreams.map(stream => ({
                        label: stream.name,
                        value: stream.id.toString()
                      }))}
                      value={field.value}
                      onValueChange={(values) => {
                        setSelectedStreams(values)
                        field.onChange(values)
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {/* Cost Fields */}
          <FormField
            control={form.control}
            name="cost_per_student"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Cost Per Student</FormLabel>
                <FormControl>
                  <Input type="number" placeholder="0.00" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="oem_transfer_price"
            render={({ field }) => (
              <FormItem>
                <FormLabel>OEM Transfer Price</FormLabel>
                <FormControl>
                  <Input type="number" placeholder="0.00" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="tax_rate"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tax Rate</FormLabel>
                <Select 
                  onValueChange={field.onChange}
                  value={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select tax rate" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {taxRates.map((tax) => (
                      <SelectItem 
                        key={tax.id} 
                        value={tax.id.toString()}>
                        {tax.rate}%
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
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select 
                  onValueChange={field.onChange} 
                  value={field.value}
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
                        className="capitalize"
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

          {/* Date Fields */}
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
        </div>

        <div className="space-y-4">
          <FormLabel>Contract Files</FormLabel>
          <FileUpload
            onFilesSelected={handleFilesSelected}
            existingFiles={mode === 'edit' ? contract?.contract_files || [] : []}
            onFileRemove={mode === 'edit' ? async (fileId) => {
              try {
                await fetch(`/api/contracts/${contract?.id}/files/${fileId}`, {
                  method: 'DELETE',
                })
                toast({
                  title: "Success",
                  description: "File deleted successfully",
                })
                setHasFileChanges(true)
                setIsDirty(true)
                router.refresh()
              } catch (error) {
                console.error('Failed to delete file:', error)
                toast({
                  title: "Error",
                  description: "Failed to delete file",
                  variant: "destructive",
                })
              }
            } : undefined}
          />
        </div>

        <div className="flex justify-between gap-4">
          <div className="flex gap-2">
            {mode === 'edit' && (
              <>
                <Button
                  type="button"
                  variant="destructive"
                  onClick={() => setShowDeleteDialog(true)}
                >
                  Delete Contract
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleArchive}
                >
                  Archive Contract
                </Button>
              </>
            )}
          </div>
          <div className="flex gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
            <Button 
              type="submit"
              disabled={mode === 'edit' && !isDirty}
            >
              {mode === 'edit' ? 'Update' : 'Create'} Contract
            </Button>
          </div>
        </div>

        {/* Delete Confirmation Dialog */}
        <ConfirmationDialog
          open={showDeleteDialog}
          onOpenChange={setShowDeleteDialog}
          onConfirm={handleDelete}
          title="Delete Contract"
          description="Are you sure you want to delete this contract? This action cannot be undone."
        />
      </form>
    </Form>
  )
} 
