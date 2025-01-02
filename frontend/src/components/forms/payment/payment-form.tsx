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
import { Textarea } from "@/components/ui/textarea"
import { Payment, Invoice } from "@/types/payment"
import { createPayment, updatePayment } from "@/service/api/payments"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const paymentFormSchema = z.object({
  invoice: z.string().min(1, "Invoice is required"),
  name: z.string().min(1, "Name is required"),
  amount: z.string().min(1, "Amount is required"),
  payment_date: z.string().min(1, "Payment date is required"),
  payment_method: z.enum(['cash', 'bank_transfer', 'cheque', 'upi'], {
    required_error: "Payment method is required",
  }),
  status: z.enum(['pending', 'completed', 'failed'], {
    required_error: "Status is required",
  }),
  transaction_reference: z.string().optional(),
  notes: z.string().optional(),
})

type PaymentFormValues = z.infer<typeof paymentFormSchema>

interface PaymentFormProps {
  mode?: 'create' | 'edit'
  payment?: Payment
  invoices: Invoice[]
}

export function PaymentForm({ mode = 'create', payment, invoices }: PaymentFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentFormSchema),
    defaultValues: {
      invoice: payment?.invoice?.toString() ?? "",
      name: payment?.name ?? "",
      amount: payment?.amount?.toString() ?? "",
      payment_date: payment?.payment_date ?? new Date().toISOString().split('T')[0],
      payment_method: payment?.payment_method ?? "cash",
      status: payment?.status ?? "pending",
      transaction_reference: payment?.transaction_reference ?? "",
      notes: payment?.notes ?? "",
    },
  })

  async function onSubmit(data: PaymentFormValues) {
    try {
      setIsSubmitting(true)
      if (mode === 'edit' && payment) {
        await updatePayment(payment.id.toString(), data)
        toast({
          title: "Success",
          description: "Payment updated successfully",
        })
      } else {
        await createPayment(data)
        toast({
          title: "Success",
          description: "Payment created successfully",
        })
      }
      router.push('/payments')
      router.refresh()
    } catch (error) {
      console.error(`Failed to ${mode} payment:`, error)
      toast({
        title: "Error",
        description: `Failed to ${mode} payment`,
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="invoice"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Invoice</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select invoice" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {invoices.map((invoice) => (
                      <SelectItem key={invoice.id} value={invoice.id.toString()}>
                        Invoice #{invoice.id} - ₹{parseFloat(invoice.amount).toLocaleString('en-IN')}
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
                  <Input {...field} placeholder="Enter payment name" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="amount"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Amount</FormLabel>
                <FormControl>
                  <Input type="number" step="0.01" placeholder="Enter amount" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="payment_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Payment Date</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="payment_method"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Payment Method</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select payment method" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                    <SelectItem value="cheque">Cheque</SelectItem>
                    <SelectItem value="upi">UPI</SelectItem>
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
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="transaction_reference"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Transaction Reference</FormLabel>
                <FormControl>
                  <Input placeholder="Enter transaction reference (optional)" {...field} />
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
          <Button type="submit" disabled={isSubmitting}>
            {mode === 'edit' ? 'Update Payment' : 'Create Payment'}
          </Button>
        </div>
      </form>
    </Form>
  )
} 