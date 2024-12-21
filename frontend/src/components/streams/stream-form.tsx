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
import { Stream } from "@/types/contract"
import { createStream, updateStream } from "@/lib/api/streams"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const streamFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  duration: z.string()
    .min(1, "Duration is required")
    .transform(val => parseInt(val))
    .refine(val => val > 0, "Duration must be greater than 0"),
  duration_unit: z.enum(["months", "years", "semesters"]),
  description: z.string().min(1, "Description is required"),
})

type StreamFormValues = z.infer<typeof streamFormSchema>

interface StreamFormProps {
  mode?: 'create' | 'edit'
  stream?: Stream
  universityId: string
}

const durationUnits = [
  { label: "Months", value: "months" },
  { label: "Years", value: "years" },
  { label: "Semesters", value: "semesters" },
]

export function StreamForm({ mode = 'create', stream, universityId }: StreamFormProps) {
  const router = useRouter()
  const { toast } = useToast()

  const form = useForm<StreamFormValues>({
    resolver: zodResolver(streamFormSchema),
    defaultValues: {
      name: stream?.name ?? "",
      duration: stream?.duration?.toString() ?? "",
      duration_unit: stream?.duration_unit ?? "years",
      description: stream?.description ?? "",
    },
  })

  const { isDirty, isValid } = form.formState

  async function onSubmit(data: StreamFormValues) {
    try {
      if (mode === 'edit' && stream) {
        await updateStream(stream.id.toString(), data)
        toast({
          title: "Success",
          description: "Stream updated successfully",
        })
      } else {
        await createStream(universityId, data)
        toast({
          title: "Success",
          description: "Stream created successfully",
        })
      }
      router.push(`/universities/${universityId}/streams`)
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} stream:`, error)
      toast({
        title: "Error",
        description: `Failed to ${mode} stream`,
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
                  <Input placeholder="Enter stream name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="duration"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Duration</FormLabel>
                  <FormControl>
                    <Input 
                      type="number" 
                      placeholder="Enter duration" 
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
              name="duration_unit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Unit</FormLabel>
                  <Select 
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select unit" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {durationUnits.map((unit) => (
                        <SelectItem 
                          key={unit.value} 
                          value={unit.value}
                        >
                          {unit.label}
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
            name="description"
            render={({ field }) => (
              <FormItem className="col-span-2">
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Textarea 
                    placeholder="Enter stream description"
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
            {mode === 'edit' ? 'Update' : 'Create'} Stream
          </Button>
        </div>
      </form>
    </Form>
  )
} 