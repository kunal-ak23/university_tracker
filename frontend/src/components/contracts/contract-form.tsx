"use client"

import { useState, useEffect } from "react"
import { Contract, ContractFormData, contractFormSchema, OEM, Program, Stream, University } from "@/types/contract"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useRouter } from "next/navigation"
import { MultiSelect } from "@/components/ui/multi-select"
import { getProgramsByOem } from "@/service/api/programs"
import { getStreamsByUniversity } from "@/service/api/streams"
import { useToast } from "@/hooks/use-toast"


interface ContractFormProps {
  contract?: Contract
  oems: OEM[]
  universities: University[]
  initialStreams: Stream[]
  initialPrograms: Program[]
  action: (formData: ContractFormData) => Promise<void>
}

export function ContractForm({ 
  contract, 
  oems, 
  universities, 
  initialStreams,
  initialPrograms,
  action 
}: ContractFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [availablePrograms, setAvailablePrograms] = useState<Program[]>(initialPrograms)
  const [availableStreams, setAvailableStreams] = useState<Stream[]>(initialStreams)
  const [, setIsLoadingStreams] = useState(false)
  const [, ] = useState(false)
  const [, ] = useState<string | null>(null)

  const form = useForm<ContractFormData>({
    resolver: zodResolver(contractFormSchema),
    defaultValues: {
      name: contract?.name ?? "",
      cost_per_student: contract?.cost_per_student ?? "",
      oem_transfer_price: contract?.oem_transfer_price ?? "",
      start_date: contract?.start_date ?? "",
      end_date: contract?.end_date ?? "",
      notes: contract?.notes ?? "",
      status: contract?.status as "active" | "pending" | "expired" | undefined ?? "pending",
      tax_rate: contract?.tax_rate ?? 1,
      oem_id: contract?.oem?.id ?? 1,
      university_id: contract?.university?.id ?? 1,
      streams_ids: contract?.streams.map(s => s.id) ?? [],
      programs_ids: contract?.programs.map(p => p.id) ?? [],
    },
  })

  const handleOemChange = async (oemId: number) => {
    form.setValue('oem_id', oemId)
    form.setValue('programs_ids', []) // Clear selected programs
    
    try {
      const programs = await getProgramsByOem(oemId)
      setAvailablePrograms(programs.results)
    } catch (error) {
      console.error('Failed to load programs:', error)
    }
  }

  const handleUniversityChange = async (universityId: number) => {
    setIsLoadingStreams(true)
    try {
      form.setValue('university_id', universityId)
      form.setValue('streams_ids', [])
      const streams = await getStreamsByUniversity(universityId.toString())
      // @ts-ignore
      setAvailableStreams(streams.results as Stream[])
    } catch (error) {
      console.error('Failed to load streams:', error)
    } finally {
      setIsLoadingStreams(false)
    }
  }

  useEffect(() => {
    let mounted = true

    if (contract) {
      const loadInitialData = async () => {
        if (contract.oem?.id) {
          try {
            const programs = await getProgramsByOem(contract.oem.id)
            if (mounted) {
              setAvailablePrograms(programs.results)
            }
          } catch (error) {
            console.error(error)
          }
        }
      }
      loadInitialData()
    }

    return () => {
      mounted = false
    }
  }, [contract])

  const handleSubmit = async (formData: ContractFormData) => {
    try {
      const data = {
        ...formData,
        streams_ids: formData.streams_ids,
        programs_ids: formData.programs_ids,
        tax_rate: Number(formData.tax_rate),
        oem_id: Number(formData.oem_id),
        university_id: Number(formData.university_id)
      }
      await action(data)
      toast({
        title: "Success",
        description: "Contract updated successfully",
        variant: "default",
      })
      router.push("/contracts")
    } catch (error) {
      console.error("Failed to save contract:", error)
      toast({
        title: "Error",
        description: "Failed to update contract",
        variant: "destructive",
      })
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Contract Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="oem_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>OEM</FormLabel>
                <Select
                  onValueChange={(value) => handleOemChange(Number(value))}
                  defaultValue={String(field.value)}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select OEM" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {oems.map((oem) => (
                      <SelectItem key={oem.id} value={String(oem.id)}>
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
            name="university_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>University</FormLabel>
                <Select
                  onValueChange={(value) => handleUniversityChange(Number(value))}
                  defaultValue={String(field.value)}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select University" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {universities.map((university) => (
                      <SelectItem key={university.id} value={String(university.id)}>
                        {university.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="streams_ids"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Streams</FormLabel>
              <MultiSelect
                options={(availableStreams || []).map(stream => ({
                  label: stream.name,
                  value: String(stream.id)
                }))}
                value={field.value?.map(String) || []}
                onValueChange={(values) => field.onChange(values.map(Number))}
                placeholder="Select streams"
              />
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="programs_ids"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Programs</FormLabel>
              <MultiSelect
                options={(availablePrograms || []).map(program => ({
                  label: program.name,
                  value: String(program.id)
                }))}
                value={field.value?.map(String) || []}
                onValueChange={(values) => field.onChange(values.map(Number))}
                placeholder="Select programs"
              />
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="cost_per_student"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Cost Per Student</FormLabel>
                <FormControl>
                  <Input type="number" step="0.01" {...field} />
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
                  <Input type="number" step="0.01" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
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

        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes</FormLabel>
              <FormControl>
                <Textarea {...field} />
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
            {contract ? "Update Contract" : "Create Contract"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
