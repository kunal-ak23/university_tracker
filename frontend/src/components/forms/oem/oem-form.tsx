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
import { OEM } from "@/types/oem"
import { createOEM, updateOEM } from "@/service/api/oems"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { getEligiblePOCs, User } from "@/service/api/users"
import { useState, useEffect } from "react"

const oemFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  website: z.string().url("Must be a valid URL"),
  contact_email: z.string().email("Must be a valid email"),
  contact_phone: z.string().optional().or(z.literal("")),
  address: z.string().optional().or(z.literal("")),
  poc: z.string().min(1, "Point of Contact is required"),
})

type OEMFormValues = z.infer<typeof oemFormSchema>

interface OEMFormProps {
  mode?: 'create' | 'edit'
  oem?: OEM
}

export function OEMForm({ mode = 'create', oem }: OEMFormProps) {
  const router = useRouter()
  const { toast } = useToast()

  const [pocs, setPocs] = useState<User[]>([])

  useEffect(() => {
    async function fetchPOCs() {
      try {
        const eligiblePOCs = await getEligiblePOCs('provider')
        setPocs(eligiblePOCs.results)
      } catch (error) {
        console.error(error);
        toast({
          title: "Error",
          description: "Failed to load eligible POCs",
          variant: "destructive",
        })
      }
    }
    fetchPOCs()
  }, [toast])

  const form = useForm<OEMFormValues>({
    resolver: zodResolver(oemFormSchema),
    mode: "all",
    reValidateMode: "onChange",
    defaultValues: {
      name: oem?.name ?? "",
      website: oem?.website ?? "",
      contact_email: oem?.contact_email ?? "",
      contact_phone: oem?.contact_phone ?? "",
      address: oem?.address ?? "",
      poc: oem?.poc?.toString() ?? "",
    },
  })

  const { isDirty, isValid, errors } = form.formState

  async function onSubmit(data: OEMFormValues) {
    try {
      if (mode === 'edit' && oem) {
        await updateOEM(oem.id, data)
        toast({
          title: "Success",
          description: "OEM updated successfully",
        })
      } else {
        await createOEM(data)
        toast({
          title: "Success",
          description: "OEM created successfully",
        })
      }
      router.push('/oems')
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} OEM:`, error)
      
      // Handle server validation errors
      if (error instanceof Error) {
        try {
          const errorData = JSON.parse(error.message)
          
          // Set server-side validation errors in the form
          if (typeof errorData === 'object') {
            Object.keys(errorData).forEach((key) => {
              const messages = errorData[key]
              if (Array.isArray(messages)) {
                form.setError(key as keyof OEMFormValues, {
                  type: 'server',
                  message: messages.join(', ')
                })
              } else if (typeof messages === 'string') {
                form.setError(key as keyof OEMFormValues, {
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
            description: errorMessage || `Failed to ${mode} OEM`,
            variant: "destructive",
          })
        } catch {
          // If error message isn't JSON, show it directly
          toast({
            title: "Error",
            description: error.message || `Failed to ${mode} OEM`,
            variant: "destructive",
          })
        }
      } else {
        toast({
          title: "Error",
          description: `Failed to ${mode} OEM`,
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
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter OEM name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="website"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Website</FormLabel>
                <FormControl>
                  <Input placeholder="https://example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="contact_email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contact Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="contact@example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="contact_phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contact Phone</FormLabel>
                <FormControl>
                  <Input placeholder="+91 1234512345" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="address"
            render={({ field }) => (
              <FormItem className="col-span-2">
                <FormLabel>Address</FormLabel>
                <FormControl>
                  <Textarea 
                    placeholder="Enter address"
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
            name="poc"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Point of Contact</FormLabel>
                <Select 
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                  value={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue>
                        {field.value 
                          ? pocs.find(p => p.id.toString() === field.value)?.full_name || "Select a POC" 
                          : "Select a POC"
                        }
                      </SelectValue>
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {pocs.map((poc) => (
                      <SelectItem 
                        key={poc.id} 
                        value={poc.id.toString()}
                      >
                        {poc.full_name || poc.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
            {mode === 'edit' ? 'Update' : 'Create'} OEM
          </Button>
        </div>
      </form>
    </Form>
  )
} 
