"use client"

import { Contract } from "@/types/contract"
import { formatCurrency } from "@/lib/utils"
import { formatDate } from "@/lib/utils"
import Link from "next/link"

interface ContractsTableProps {
  contracts: Contract[]
}

export function ContractsTable({ contracts }: ContractsTableProps) {
  return (
    <div className="rounded-md border">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="p-4 text-left">Name</th>
            <th className="p-4 text-left">OEM</th>
            <th className="p-4 text-left">Cost Per Student</th>
            <th className="p-4 text-left">Status</th>
            <th className="p-4 text-left">Start Date</th>
            <th className="p-4 text-left">End Date</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map((contract) => (
            <tr key={contract.id} className="border-b">
              <td className="p-4">
                <Link href={`/contracts/${contract.id}`} className="hover:underline">
                  {contract.name}
                </Link>
              </td>
              <td className="p-4">{contract.oem.name}</td>
              <td className="p-4">{formatCurrency(parseFloat(contract.cost_per_student))}</td>
              <td className="p-4">
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                  ${contract.status === 'active' ? 'bg-green-100 text-green-800' : 
                    contract.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-red-100 text-red-800'}`}>
                  {contract.status}
                </span>
              </td>
              <td className="p-4">{formatDate(contract.start_date)}</td>
              <td className="p-4">{formatDate(contract.end_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
} 