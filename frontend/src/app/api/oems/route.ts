import { apiFetch } from "@/lib/api/fetch"

export async function GET() {
  const oems = await apiFetch('/oems/')
  return Response.json(oems)
} 