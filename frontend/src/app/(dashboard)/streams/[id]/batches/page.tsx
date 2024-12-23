import { getBatchesByStream } from "@/lib/api/batches"
import BatchesList from "./batches-list"

export default async function BatchesPage({
  params,
}: {
  params: { id: string }
}) {
  const id = params.id
  const batches = (await getBatchesByStream(id)).results

  return <BatchesList initialBatches={batches} streamId={id} />
}