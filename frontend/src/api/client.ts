const TOKEN_KEY = 'starmarket_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  // Populated only for the POST /strategies validation-failure shape
  // (detail: {message, issues}); every other error path leaves this empty.
  issues: { severity: string; code: string; message: string }[]
  constructor(message: string, status: number, issues: { severity: string; code: string; message: string }[] = []) {
    super(message)
    this.status = status
    this.issues = issues
  }
}

// Some error paths return a plain string `detail`, others (POST /strategies
// validation failures) return `detail: {message, issues}` — normalize both.
function extractErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String((detail as { message: unknown }).message)
  }
  return fallback
}

function extractIssues(detail: unknown): { severity: string; code: string; message: string }[] {
  if (detail && typeof detail === 'object' && Array.isArray((detail as { issues?: unknown }).issues)) {
    return (detail as { issues: { severity: string; code: string; message: string }[] }).issues
  }
  return []
}

interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { ...options.headers }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await fetch(`/api${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (response.status === 401) {
    clearToken()
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    throw new ApiError('Not authenticated', 401)
  }

  if (!response.ok) {
    let detail: unknown = null
    try {
      const body = await response.json()
      detail = body.detail
    } catch {
      // non-JSON error body, fall through to generic message
    }
    throw new ApiError(
      extractErrorMessage(detail, `Request failed (${response.status})`),
      response.status,
      extractIssues(detail),
    )
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
