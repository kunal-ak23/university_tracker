import { getBatchesByStream } from "@/service/api/batches"
import BatchesList from "./batches-list"

export default async function BatchesPage({params}: {params: Promise<{
  id: string
}>}) {
  const {id} = await params;
  const batches = (await getBatchesByStream(id)).results

  return <BatchesList initialBatches={batches} streamId={id} />
}
