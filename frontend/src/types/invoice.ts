export interface InvoiceFormData {
  billing: number
  issue_date: string
  due_date: string
  amount: string
  notes?: string
  proforma_invoice?: File
  actual_invoice?: File
  status: 'unpaid' | 'paid' | 'partially_paid' | 'overdue' | 'cancelled'
} 