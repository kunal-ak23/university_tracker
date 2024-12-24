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
import { Program, DurationUnit } from "@/types/program"
import { createProgram, updateProgram } from "@/lib/api/programs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useEffect, useState } from "react"
import { OEM } from "@/types/oem"
import { getOEMs } from "@/lib/api/oems"

const programFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  program_code: z.string().min(1, "Program code is required"),
  duration: z.coerce.number().min(1, "Duration must be at least 1"),
  duration_unit: z.enum(["Years", "Months", "Weeks", "Days"], {
    required_error: "Please select a duration unit",
  }),
  description: z.string().optional(),
  prerequisites: z.string().optional(),
  provider_id: z.coerce.number().min(1, "Provider is required"),
})

type ProgramFormValues = z.infer<typeof programFormSchema>

interface ProgramFormProps {
  mode?: 'create' | 'edit'
  program?: Program
  providerId?: number
}

const durationUnits: DurationUnit[] = ["Years", "Months", "Weeks", "Days"]

function generateProgramCode(oemName: string, programName: string): string {
  // Remove special characters and convert to uppercase
  const cleanOEM = oemName.replace(/[^a-zA-Z0-9\s]/g, '').toUpperCase()
  const cleanProgram = programName.replace(/[^a-zA-Z0-9\s]/g, '').toUpperCase()
  
  // Take first 3 characters of OEM name (or all if less than 3)
  const oemPrefix = cleanOEM.split(/\s+/)[0].slice(0, 3)
  
  // Split program name on spaces and take first 3 chars of each word
  const programWords = cleanProgram.split(/\s+/).filter(word => word.length > 0)
  const programSuffix = programWords
    .map(word => word.slice(0, 3))
    .join('_')
  
  return `${oemPrefix}_${programSuffix}`
}

export function ProgramForm({ mode = 'create', program, providerId }: ProgramFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [oems, setOEMs] = useState<OEM[]>([])
  const [selectedOEM, setSelectedOEM] = useState<OEM | undefined>(
    program?.provider ?? oems.find(oem => oem.id.toString() === providerId?.toString())
  )

  useEffect(() => {
    async function fetchOEMs() {
      try {
        const response = await getOEMs({ page_size: 100 })
        setOEMs(response.results)
        // Set selected OEM if providerId is provided
        if (providerId) {
          const oem = response.results.find(oem => oem.id.toString() === providerId.toString())
          setSelectedOEM(oem)
        }
      } catch (error) {
        console.error('Failed to fetch OEMs:', error)
        toast({
          title: "Error",
          description: "Failed to load OEMs",
          variant: "destructive",
        })
      }
    }
    fetchOEMs()
  }, [toast, providerId])

  const form = useForm<ProgramFormValues>({
    resolver: zodResolver(programFormSchema),
    mode: "all",
    reValidateMode: "onChange",
    defaultValues: {
      name: program?.name ?? "",
      program_code: program?.program_code ?? "",
      duration: program?.duration ?? 1,
      duration_unit: program?.duration_unit as DurationUnit ?? "Years",
      description: program?.description ?? "",
      prerequisites: program?.prerequisites ?? "",
      provider_id: program?.provider?.id ?? providerId ?? undefined,
    },
  })

  const { isDirty, isValid } = form.formState

  // Watch for changes in provider and name to auto-generate program code
  const watchProvider = form.watch("provider_id")
  const watchName = form.watch("name")

  useEffect(() => {
    // Only auto-generate if in create mode and both fields have values
    if (mode === 'create' && watchProvider && watchName) {
      const oem = oems.find(o => o.id.toString() === watchProvider.toString())
      if (oem) {
        const generatedCode = generateProgramCode(oem.name, watchName)
        form.setValue("program_code", generatedCode, { 
          shouldDirty: true,
          shouldValidate: true 
        })
      }
    }
  }, [watchProvider, watchName, oems, mode, form])

  async function onSubmit(data: ProgramFormValues) {
    try {
      if (mode === 'edit' && program) {
        await updateProgram(program.id, data)
        toast({
          title: "Success",
          description: "Program updated successfully",
        })
        router.back()
        router.refresh()
      } else {
        await createProgram(data)
        toast({
          title: "Success",
          description: "Program created successfully",
        })
        router.back()
        router.refresh()
      }
    } catch (error) {
      console.error(`Failed to ${mode} program:`, error)
      
      // Handle server validation errors
      if (error instanceof Error) {
        try {
          const errorData = JSON.parse(error.message)
          
          // Set server-side validation errors in the form
          if (typeof errorData === 'object') {
            Object.keys(errorData).forEach((key) => {
              const messages = errorData[key]
              if (Array.isArray(messages)) {
                form.setError(key as keyof ProgramFormValues, {
                  type: 'server',
                  message: messages.join(', ')
                })
              } else if (typeof messages === 'string') {
                form.setError(key as keyof ProgramFormValues, {
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
            description: errorMessage || `Failed to ${mode} program`,
            variant: "destructive",
          })
        } catch {
          // If error message isn't JSON, show it directly
          toast({
            title: "Error",
            description: error.message || `Failed to ${mode} program`,
            variant: "destructive",
          })
        }
      } else {
        toast({
          title: "Error",
          description: `Failed to ${mode} program`,
          variant: "destructive",
        })
      }
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={form.control}
            name="provider_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Provider (OEM)</FormLabel>
                <Select 
                  onValueChange={(value) => {
                    field.onChange(value)
                    const oem = oems.find(o => o.id.toString() === value)
                    setSelectedOEM(oem)
                  }}
                  defaultValue={field.value?.toString()}
                  value={field.value?.toString()}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select an OEM" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {oems.map((oem) => (
                      <SelectItem 
                        key={oem.id} 
                        value={oem.id.toString()}
                      >
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
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter program name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="program_code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Program Code</FormLabel>
                <FormControl>
                  <Input 
                    placeholder="Auto-generated based on OEM and name" 
                    {...field} 
                    className="font-mono"
                  />
                </FormControl>
                {mode === 'create' && (
                  <p className="text-sm text-muted-foreground">
                    Auto-generated code can be modified if needed
                  </p>
                )}
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="duration"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Duration</FormLabel>
                <FormControl>
                  <Input 
                    type="number" 
                    min={1} 
                    placeholder="Enter duration" 
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="duration_unit"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Duration Unit</FormLabel>
                <Select 
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select duration unit" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {durationUnits.map((unit) => (
                      <SelectItem key={unit} value={unit}>
                        {unit}
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
            name="description"
            render={({ field }) => (
              <FormItem className="col-span-2">
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Textarea 
                    placeholder="Enter program description"
                    className="resize-none"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="prerequisites"
            render={({ field }) => (
              <FormItem className="col-span-2">
                <FormLabel>Prerequisites</FormLabel>
                <FormControl>
                  <Textarea 
                    placeholder="Enter program prerequisites"
                    className="resize-none"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

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
            disabled={!isDirty || !isValid}
          >
            {mode === 'edit' ? 'Update' : 'Create'} Program
          </Button>
        </div>
      </form>
    </Form>
  )
} 