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
import { University } from "@/types/university"
import { createUniversity, updateUniversity } from "@/lib/api/universities"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { getEligiblePOCs, User } from "@/lib/api/users"
import { useState, useEffect } from "react"

const universityFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  website: z.string().url("Must be a valid URL"),
  established_year: z.string()
    .regex(/^\d{4}$/, "Must be a valid year")
    .transform(val => parseInt(val))
    .refine(val => val <= new Date().getFullYear(), "Year cannot be in the future"),
  accreditation: z.string().optional().or(z.literal("")),
  contact_email: z.string().email("Must be a valid email").optional().or(z.literal("")),
  contact_phone: z.string().optional().or(z.literal("")),
  address: z.string().optional().or(z.literal("")),
  location: z.string().optional().or(z.literal("")),
  poc: z.string().min(1, "Point of Contact is required"),
})

type UniversityFormValues = z.infer<typeof universityFormSchema>

interface UniversityFormProps {
  mode?: 'create' | 'edit'
  university?: University
}

export function UniversityForm({ mode = 'create', university }: UniversityFormProps) {
  const router = useRouter()
  const { toast } = useToast()

  const [pocs, setPocs] = useState<User[]>([])

  useEffect(() => {
    async function fetchPOCs() {
      try {
        const eligiblePOCs = await getEligiblePOCs('university')

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

  const form = useForm<UniversityFormValues>({
    resolver: zodResolver(universityFormSchema),
    mode: "all",
    reValidateMode: "onChange",
    defaultValues: {
      name: university?.name ?? "",
      website: university?.website ?? "",
      established_year: university?.established_year?.toString() ?? "",
      accreditation: university?.accreditation ?? "",
      contact_email: university?.contact_email ?? "",
      contact_phone: university?.contact_phone ?? "",
      address: university?.address ?? "",
      location: university?.location ?? "",
      poc: university?.poc?.toString() ?? "",
    },
  })

  const { isDirty, isValid } = form.formState

  async function onSubmit(data: UniversityFormValues) {
    try {
      if (mode === 'edit' && university) {
        await updateUniversity(university.id, data)
        toast({
          title: "Success",
          description: "University updated successfully",
        })
      } else {
        await createUniversity(data)
        toast({
          title: "Success",
          description: "University created successfully",
        })
      }
      router.push('/universities')
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} university:`, error)
      toast({
        title: "Error",
        description: `Failed to ${mode} university`,
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
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter university name" {...field} />
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
                  <Input placeholder="https://example.edu" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="established_year"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Established Year</FormLabel>
                <FormControl>
                  <Input 
                    type="number" 
                    placeholder="YYYY" 
                    min="1800"
                    max={new Date().getFullYear()}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="accreditation"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Accreditation</FormLabel>
                <FormControl>
                  <Input placeholder="Enter accreditation details" {...field} />
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
                  <Input type="email" placeholder="contact@example.edu" {...field} />
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
                  <Input placeholder="+1234567890" {...field} />
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
                    {pocs.map((poc, index) => (
                      <SelectItem 
                        key={"poc" + index} 
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

        <div className="flex justify-end">
          <Button 
            type="submit" 
            disabled={mode === 'edit' ? (!isDirty || !isValid) : !isValid}
          >
            {mode === 'edit' ? 'Update' : 'Create'} University
          </Button>
        </div>
      </form>
    </Form>
  )
} 