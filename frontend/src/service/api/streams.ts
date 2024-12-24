
import { Stream } from "@/types/stream"
import { apiFetch } from "./fetch"
import { PaginatedResponse } from "@/types/common"

export async function getStreams(): Promise<Stream[]> {
  return apiFetch('/streams/')
}

export async function getStream(id: number): Promise<Stream> {
  return apiFetch(`/streams/${id}/`)
}

export async function getStreamsByUniversity(universityId: string): Promise<PaginatedResponse<Stream>> {
  return apiFetch(`/streams/?university=${universityId}`)
}

export async function createStream(universityId: string, data: Partial<Stream>): Promise<Stream> {
  return apiFetch('/streams/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...data,
      university: Number(universityId),
    }),
  })
}

export async function updateStream(id: string, data: Partial<Stream>): Promise<Stream> {
  return apiFetch(`/streams/${id}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function deleteStream(id: string): Promise<void> {
  return apiFetch(`/streams/${id}/`, {
    method: 'DELETE',
  })
}