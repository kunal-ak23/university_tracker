import { getContract } from "@/lib/api/contracts"
import { formatCurrency, formatDate } from "@/lib/utils"
import Link from "next/link"
import { notFound } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ExternalLink, FileText } from "lucide-react"
import { Contract } from "@/types/contract"
import { ContractActions } from "@/components/contracts/contract-actions"

export default async function ContractPage({
  params,
}: Readonly<{
params: Promise<{ id: string }>;
}>) {
  const { id } = await params;
  let contract: Contract;

  try {
    contract = await getContract(id);
  } catch (error) {
    console.error(error);
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{contract.name}</h2>
        <ContractActions 
          contractId={id} 
          status={contract.status}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">Contract Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Status</dt>
              <dd>
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                  ${contract.status === 'active' ? 'bg-green-100 text-green-800' : 
                    contract.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-red-100 text-red-800'}`}>
                  {contract.status}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Cost Per Student</dt>
              <dd>{formatCurrency(parseFloat(contract.cost_per_student))}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">OEM Transfer Price</dt>
              <dd>{formatCurrency(parseFloat(contract.oem_transfer_price))}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Start Date</dt>
              <dd>{formatDate(contract.start_date)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">End Date</dt>
              <dd>{formatDate(contract.end_date)}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="text-xl font-semibold">OEM Details</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="font-medium">Name</dt>
              <dd>{contract.oem.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="font-medium">Website</dt>
              <dd>
                <a href={contract.oem.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  {contract.oem.website}
                </a>
              </dd>
            </div>
          </dl>
        </div>

        {contract.contract_programs && contract.contract_programs?.length > 0 && (
          <div className="col-span-2 rounded-lg border p-6 space-y-4">
            <h3 className="text-xl font-semibold">Programs</h3>
            <div className="grid gap-4">
              {contract.contract_programs.map((cp, index) => (
                <div key={"contract" + index} className="rounded border p-4">
                  <h4 className="font-medium">{cp.program.name}</h4>
                  <p className="text-sm text-muted-foreground">
                    Code: {cp.program.program_code} | Duration: {cp.program.duration} {cp.program.duration_unit}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {contract.streams.length > 0 && (
          <div className="col-span-2 rounded-lg border p-6 space-y-4">
            <h3 className="text-xl font-semibold">Eligible Streams</h3>
            <div className="grid gap-4">
              {contract.streams.map((stream, index) => (
                <div key={"stream" + index} className="rounded border p-4">
                  <h4 className="font-medium">{stream.name}</h4>
                  <p className="text-sm text-muted-foreground">
                    Duration: {stream.duration} {stream.duration_unit}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {contract.contract_files && contract.contract_files?.length > 0 && (
          <div className="col-span-2 rounded-lg border p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold">Contract Files</h3>
              <Link href={`/contracts/${id}/files`}>
                <Button variant="outline" size="sm">
                  <FileText className="mr-2 h-4 w-4" />
                  Manage Files
                </Button>
              </Link>
            </div>
            <div className="grid gap-4">
              {contract.contract_files.map((file, index) => (
                <div key={"file" + index} className="rounded border p-4 flex justify-between items-center">
                  <div>
                    <h4 className="font-medium">{file.file_type}</h4>
                    {file.description && <p className="text-sm text-muted-foreground">{file.description}</p>}
                  </div>
                  <Link 
                    href={file.file}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    <Button variant="outline">
                      <ExternalLink className="h-6 w-6 mt-[2px]" />
                      Open in new tab
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 