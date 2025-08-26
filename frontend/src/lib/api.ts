import { AuthManager } from './auth'

// Use NEXT_PUBLIC_API_URL if set, otherwise use Next.js proxy for relative URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`

    // Get API key for authentication
    let apiKey: string | null = null
    try {
      // Only get API key for endpoints that require auth
      if (endpoint.startsWith('/ai/') || endpoint.startsWith('/protected/')) {
        apiKey = await AuthManager.getOrCreateSession()
      }
    } catch (error) {
      console.warn('Could not get API key:', error)
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    }

    // Add authorization header if we have an API key
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`
    }

    const config: RequestInit = {
      headers,
      ...options,
    }

    let response: Response
    try {
      response = await fetch(url, config)
    } catch (error) {
      const networkError = error as Error
      throw new Error(`Network error contacting API at ${url}: ${networkError.message || 'Connection failed'}`)
    }

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error ${response.status}: ${errorText}`)
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return response.json()
    } else {
      return response.text() as unknown as T
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(
    endpoint: string, 
    data?: any, 
    options: RequestInit = {}
  ): Promise<T> {
    let body: string | FormData
    let headers = options.headers || {}

    if (data instanceof FormData) {
      body = data
      // Don't set Content-Type for FormData, let browser set it with boundary
      delete (headers as any)['Content-Type']
    } else {
      body = JSON.stringify(data)
    }

    return this.request<T>(endpoint, {
      method: 'POST',
      body,
      headers,
      ...options,
    })
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

export const api = new ApiClient(`${API_BASE}/api`)