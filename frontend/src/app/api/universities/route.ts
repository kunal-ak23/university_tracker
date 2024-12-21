import { apiFetch } from "@/lib/api/fetch"

export async function GET() {
  const universities = await apiFetch('/universities/')
  return Response.json(universities)
} 