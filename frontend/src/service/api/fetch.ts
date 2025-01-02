/* eslint-disable @typescript-eslint/ban-ts-comment */

"use server";

import { auth } from "@/auth"


export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
) {
  const session = await auth();
  // @ts-ignore
  if (!session?.accessToken || !session?.refreshToken) {
    throw new Error('No access token found')
  }

  const baseURL = process.env.NEXT_PUBLIC_API_URL
  const url = `${baseURL}${endpoint}`

  let response
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        // @ts-ignore
        'Authorization': `Bearer ${session.accessToken}`,
        ...options.headers,
      },
    })
  } catch (error) {
    console.error('Fetch failed:', error)
    throw new Error('Network request failed', { cause: error })
  }

  if (!response) {
    throw new Error('No response received')
  }

  // If token expired, try to refresh
  // @ts-ignore
  if (response.status === 401 && session.refreshToken) {
    try {
      // Call refresh token endpoint directly
      const refreshResponse = await fetch(`${baseURL}/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // @ts-ignore
          refresh: session.refreshToken
        })
      })

      if (!refreshResponse.ok) {
        throw new Error('Refresh token expired. Please login again.')
      }

      const { access: newAccessToken } = await refreshResponse.json()
      
      // Retry original request with new token
      response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newAccessToken}`,
          ...options.headers,
        },
      })
    } catch (error) {
      throw error
    }
  }

  if (!response.ok) {
    try {
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json()
        throw new Error(JSON.stringify(errorData))
      }
      const errorText = await response.text()
      throw new Error(errorText || `API request failed with status ${response.status}`)
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('API request failed')
    }
  }

  // For DELETE requests or when no content is expected
  if (options.method === 'DELETE' || response.status === 204) {
    return null
  }

  try {
    // Check if response has content before parsing JSON
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }
    return null;
  } catch (error) {
    console.error('JSON parsing failed:', error)
    throw new Error('Failed to parse response')
  }
}

export async function postFormData(
  endpoint: string,
  formData: FormData,
  options: RequestInit = {}
) {
  const session = await auth()
  // @ts-ignore
  if (!session?.accessToken) {
    throw new Error('No access token found')
  }

  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  const url = `${baseURL}${endpoint}`;

  let response = await fetch(url, {
    ...options,
    body: formData,
    headers: {
      // @ts-ignore
      'Authorization': `Bearer ${session.accessToken}`,
      ...options.headers,
    },
  })

  // If token expired, try to refresh
  // @ts-ignore
  if (response.status === 401 && session.refreshToken) {
    try {
      // Call refresh token endpoint directly
      const refreshResponse = await fetch(`${baseURL}/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // @ts-ignore 
          refresh: session.refreshToken
        })
      })

      if (!refreshResponse.ok) {
        throw new Error('Refresh token expired. Please login again.')
      }

      const { access: newAccessToken } = await refreshResponse.json()
      
      // Retry original request with new token
      response = await fetch(url, {
        ...options,
        body: formData,
        headers: {
          'Authorization': `Bearer ${newAccessToken}`,
          ...options.headers,
        },
      })
    } catch (error) {
      throw error
    }
  }

  if (!response.ok) {
    
    try {
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json()
        throw new Error(JSON.stringify(errorData))
      }
      const errorText = await response.text()
      throw new Error(errorText || `API request failed with status ${response.status}`)
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('API request failed')
    }
  }

  return response.json()
} 