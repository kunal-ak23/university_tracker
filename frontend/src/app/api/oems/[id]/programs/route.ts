import { apiFetch } from "@/lib/api/fetch"
import { NextRequest } from "next/server"

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const {id} = params;
    const programs = await apiFetch(`/programs/?oem=${id}`)
    return Response.json(programs)
  } catch (error) {
    console.error('Failed to fetch OEM programs:', error)
    return new Response('Failed to fetch programs', { status: 500 })
  }
} 