import { apiFetch } from "@/lib/api/fetch"
import { NextRequest } from "next/server"

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const {id} = params;
  try {
    const streams = await apiFetch(`/streams/?university=${id}`)
    return Response.json(streams)
  } catch (error) {
    console.error('Failed to fetch university streams:', error)
    return new Response('Failed to fetch streams', { status: 500 })
  }
} 