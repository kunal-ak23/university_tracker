import { apiFetch } from "@/lib/api/fetch"
import { NextRequest } from "next/server"

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string; fileId: string } }
) {
  const {id, fileId} = params;
  try {
    await apiFetch(`/contracts/${id}/files/${fileId}/`, {
      method: 'DELETE',
    })
    return new Response(null, { status: 204 })
  } catch (error) {
    console.error('Failed to delete file:', error)
    return new Response('Failed to delete file', { status: 500 })
  }
} 