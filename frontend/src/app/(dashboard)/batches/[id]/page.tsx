import { getBatch } from "@/lib/api/batches"
import { getContract } from "@/lib/api/contracts"
import BatchDetail from "./batch-detail"

const BatchDetailPage = async ({params}:  {params: Promise<{
  id: string
}>}) => {
  const {id} = await params;
  const batch = await getBatch(id);
  const contract = await getContract(batch.contract.toString());

  return <BatchDetail initialBatch={batch} initialContract={contract} />  
}

export default BatchDetailPage;