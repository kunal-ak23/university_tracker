"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command"
import { useToast } from "@/hooks/use-toast"
import { createInvoice, updateInvoice } from "@/service/api/invoices"
import { getBillings } from "@/service/api/billings"
import { Billing } from "@/types/billing"
import { CalendarIcon, Check, ChevronsUpDown, Loader2 } from "lucide-react"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Label } from "@/components/ui/label"
import { format } from "date-fns"
import { cn } from "@/service/utils"
import { Invoice } from "@/types/payment"


const formSchema = z.object({
  billing: z.string(),
  name: z.string().min(1, "Name is required"),
  issue_date: z.date(),
  due_date: z.date(),
  amount: z.coerce.number().min(0),
  amount_paid: z.coerce.number().min(0).default(0),
  status: z.enum(['unpaid', 'paid', 'partially_paid', 'overdue', 'cancelled']),
  notes: z.string().optional(),
  proforma_invoice: z.instanceof(File).optional(),
  actual_invoice: z.instanceof(File).optional(),
})

type FormData = z.infer<typeof formSchema>

interface InvoiceFormProps {
  invoice?: Invoice
}

export function InvoiceForm({ invoice }: InvoiceFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [billings, setBillings] = useState<Billing[]>([])
  const [open, setOpen] = useState(false)
  const [searchValue, setSearchValue] = useState("")
  const [proformaInvoice, setProformaInvoice] = useState<File | null>(null)
  const [actualInvoice, setActualInvoice] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingBillings, setIsLoadingBillings] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      billing: invoice?.billing ? String(invoice.billing) : '',
      name: invoice?.name || '',
      issue_date: invoice?.issue_date ? new Date(invoice.issue_date) : new Date(),
      due_date: invoice?.due_date ? new Date(invoice.due_date) : new Date(),
      amount: Number(invoice?.amount) || 0,
      amount_paid: Number(invoice?.amount_paid) || 0,
      status: invoice?.status || 'unpaid',
      notes: invoice?.notes || '',
    },
  })

  const loadBillings = async (page: number, search?: string) => {
    try {
      setIsLoadingBillings(true)
      const response = await getBillings({
        page,
        search,
        status: 'active',
        page_size: 10
      })
      if (page === 1) {
        setBillings(response.results)
      } else {
        setBillings(prev => [...prev, ...response.results])
      }
      setHasMore(!!response.next)
    } catch (error) {
      console.error('Failed to fetch billings:', error)
      toast({
        title: "Error",
        description: "Failed to load billings",
        variant: "destructive",
      })
    } finally {
      setIsLoadingBillings(false)
    }
  }

  // Load initial billings
  useEffect(() => {
    loadBillings(1)
  }, [])

  // Handle search
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentPage(1)
      loadBillings(1, searchValue)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchValue])

  // Handle scroll in dropdown
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const bottom = e.currentTarget.scrollHeight - e.currentTarget.scrollTop === e.currentTarget.clientHeight
    if (bottom && hasMore && !isLoadingBillings) {
      const nextPage = currentPage + 1
      setCurrentPage(nextPage)
      loadBillings(nextPage, searchValue)
    }
  }

  const onSubmit = async (values: FormData) => {
    if (isSubmitting) return
    setIsSubmitting(true)

    try {
      const formData = new FormData()
      formData.append('billing', values.billing)
      formData.append('name', values.name)
      formData.append('issue_date', format(values.issue_date, 'yyyy-MM-dd'))
      formData.append('due_date', format(values.due_date, 'yyyy-MM-dd'))
      formData.append('amount', Number(values.amount).toFixed(2))
      formData.append('amount_paid', Number(values.amount_paid).toFixed(2))
      formData.append('status', values.status)
      if (values.notes) {
        formData.append('notes', values.notes)
      }
      
      // Add files to FormData if they exist
      if (proformaInvoice) {
        formData.append('proforma_invoice', proformaInvoice)
      }
      if (actualInvoice) {
        formData.append('actual_invoice', actualInvoice)
      }

      try {
        if (invoice) {
          await updateInvoice(invoice.id, formData)
          toast({
            title: "Success",
            description: "Invoice updated successfully",
          })
        } else {
          await createInvoice(formData)
          toast({
            title: "Success",
            description: "Invoice created successfully",
          })
        }

        router.push('/invoices')
        router.refresh()
      } catch (error) {
        console.error('API Error:', error)
        if (error instanceof Error) {
          try {
            const errorData = JSON.parse(error.message)
            // Set field errors in the form
            Object.keys(errorData).forEach((key) => {
              form.setError(key as any, {
                type: 'manual',
                message: Array.isArray(errorData[key]) ? errorData[key][0] : errorData[key],
              })
            })
            // Show first error in toast
            const firstErrorField = Object.keys(errorData)[0]
            const firstError = Array.isArray(errorData[firstErrorField]) 
              ? errorData[firstErrorField][0] 
              : errorData[firstErrorField]
            toast({
              title: "Validation Error",
              description: `${firstErrorField}: ${firstError}`,
              variant: "destructive",
            })
          } catch {
            // If error message isn't JSON, show the raw error
            toast({
              title: "Error",
              description: error.message || "Failed to save invoice",
              variant: "destructive",
            })
          }
        } else {
          toast({
            title: "Error",
            description: "An unexpected error occurred",
            variant: "destructive",
          })
        }
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
  const ACCEPTED_FILE_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]

  const validateFile = (file: File) => {
    if (file.size > MAX_FILE_SIZE) {
      return 'File size should be less than 5MB'
    }
    if (!ACCEPTED_FILE_TYPES.includes(file.type)) {
      return 'File type should be PDF or Word document'
    }
    return null
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {/* Name (66%) and Billing (33%) row */}
        <div className="grid grid-cols-3 gap-4">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem className="col-span-2">
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input {...field} placeholder="Enter invoice name" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="billing"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Billing</FormLabel>
                <Popover open={open} onOpenChange={setOpen}>
                  <PopoverTrigger asChild>
                    <FormControl>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className={cn(
                          "w-full justify-between",
                          !field.value && "text-muted-foreground"
                        )}
                      >
                        {field.value
                          ? billings.find((billing) => String(billing.id) === field.value)?.name
                          : "Select billing"}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </FormControl>
                  </PopoverTrigger>
                  <PopoverContent className="w-[400px] p-0">
                    <Command>
                      <CommandInput
                        placeholder="Search billing..."
                        value={searchValue}
                        onValueChange={setSearchValue}
                      />
                      <CommandEmpty>No billing found.</CommandEmpty>
                      <CommandGroup className="max-h-[300px] overflow-auto" onScroll={handleScroll}>
                        {billings.map((billing) => (
                          <CommandItem
                            key={billing.id}
                            value={billing.id.toString()}
                            onSelect={() => {
                              form.setValue('billing', String(billing.id))
                              setOpen(false)
                              setSearchValue("")
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                String(billing.id) === field.value
                                  ? "opacity-100"
                                  : "opacity-0"
                              )}
                            />
                            {billing.name}
                          </CommandItem>
                        ))}
                        {isLoadingBillings && (
                          <div className="flex items-center justify-center p-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </div>
                        )}
                      </CommandGroup>
                    </Command>
                  </PopoverContent>
                </Popover>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Issue date, Due date, and Status (33% each) */}
        <div className="grid grid-cols-3 gap-4">
          <FormField
            control={form.control}
            name="issue_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Issue Date</FormLabel>
                <Popover>
                  <PopoverTrigger asChild>
                    <FormControl>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full pl-3 text-left font-normal",
                          !field.value && "text-muted-foreground"
                        )}
                      >
                        {field.value ? (
                          format(field.value, "PPP")
                        ) : (
                          <span>Pick a date</span>
                        )}
                        <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                      </Button>
                    </FormControl>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={field.value}
                      onSelect={field.onChange}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="due_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Due Date</FormLabel>
                <Popover>
                  <PopoverTrigger asChild>
                    <FormControl>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full pl-3 text-left font-normal",
                          !field.value && "text-muted-foreground"
                        )}
                      >
                        {field.value ? (
                          format(field.value, "PPP")
                        ) : (
                          <span>Pick a date</span>
                        )}
                        <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                      </Button>
                    </FormControl>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={field.value}
                      onSelect={field.onChange}
                      disabled={(date: Date) =>
                        date < new Date()
                      }
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
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
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="unpaid">Unpaid</SelectItem>
                    <SelectItem value="paid">Paid</SelectItem>
                    <SelectItem value="partially_paid">Partially Paid</SelectItem>
                    <SelectItem value="overdue">Overdue</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Amount field */}
        <FormField
          control={form.control}
          name="amount"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Amount</FormLabel>
              <FormControl>
                <Input type="number" step="0.01" placeholder="0.00" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Proforma and Actual Invoice (50% each) */}
        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label>Proforma Invoice</Label>
            <Input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  const error = validateFile(file)
                  if (error) {
                    toast({
                      title: "Error",
                      description: error,
                      variant: "destructive",
                    })
                    e.target.value = ''
                    return
                  }
                  setProformaInvoice(file)
                }
              }}
            />
            {invoice?.proforma_invoice && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Button
                  type="button"
                  variant="link"
                  className="h-auto p-0 text-blue-500"
                  onClick={() => window.open(invoice.proforma_invoice as string, '_blank')}
                >
                  View Current Proforma Invoice
                </Button>
              </div>
            )}
          </div>

          <div className="grid gap-2">
            <Label>Actual Invoice</Label>
            <Input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  const error = validateFile(file)
                  if (error) {
                    toast({
                      title: "Error",
                      description: error,
                      variant: "destructive",
                    })
                    e.target.value = ''
                    return
                  }
                  setActualInvoice(file)
                }
              }}
            />
            {invoice?.actual_invoice && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Button
                  type="button"
                  variant="link"
                  className="h-auto p-0 text-blue-500"
                  onClick={() => window.open(invoice.actual_invoice as string, '_blank')}
                >
                  View Current Actual Invoice
                </Button>
              </div>
            )}
          </div>
        </div>

        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes</FormLabel>
              <FormControl>
                <Textarea placeholder="Add any additional notes here..." {...field} />
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
          <Button type="submit" disabled={isSubmitting}>
            {invoice ? 'Update Invoice' : 'Create Invoice'}
          </Button>
        </div>
      </form>
    </Form>
  )
} 