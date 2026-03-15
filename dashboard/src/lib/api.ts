import type {
  CostsResponse,
  FailureStats,
  HealthResponse,
  OverviewStats,
  SessionDetail,
  SessionSummary,
  TraceRead,
} from './types'

const rawApiBaseUrl = import.meta.env.VITE_LENS_API_URL ?? 'http://localhost:8100'

export const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, '')

export const TRACE_STREAM_URL = (() => {
  const url = new URL(API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws/traces'
  return url.toString()
})()

type RequestOptions = {
  method?: 'GET' | 'POST'
  body?: unknown
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>) {
  const url = new URL(path, API_BASE_URL)
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value === undefined || value === '') {
      continue
    }
    url.searchParams.set(key, String(value))
  }
  return url.toString()
}

async function request<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  options?: RequestOptions,
) {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options?.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(buildUrl(path, params), {
    method: options?.method ?? 'GET',
    headers,
    body: options?.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return (await response.json()) as T
}

export function getHealth() {
  return request<HealthResponse>('/api/v1/health')
}

export function getOverviewStats(days?: number) {
  return request<OverviewStats>('/api/v1/stats/overview', { days })
}

export function getTraces(params?: {
  provider?: string
  model?: string
  status?: string
  sessionId?: string
  days?: number
  limit?: number
  offset?: number
}) {
  return request<TraceRead[]>('/api/v1/traces', {
    provider: params?.provider,
    model: params?.model,
    status: params?.status,
    session_id: params?.sessionId,
    days: params?.days,
    limit: params?.limit,
    offset: params?.offset,
  })
}

export function getSessions(params?: { limit?: number; offset?: number }) {
  return request<SessionSummary[]>('/api/v1/sessions', {
    limit: params?.limit,
    offset: params?.offset,
  })
}

export function getSessionDetail(sessionId: string) {
  return request<SessionDetail>(`/api/v1/sessions/${encodeURIComponent(sessionId)}`)
}

export function getFailureStats(limit?: number) {
  return request<FailureStats>('/api/v1/stats/failures', { limit })
}

export function getCosts(params: {
  groupBy: 'day' | 'provider' | 'model'
  provider?: string
  model?: string
  sessionId?: string
  days?: number
}) {
  return request<CostsResponse>('/api/v1/stats/costs', {
    group_by: params.groupBy,
    provider: params.provider,
    model: params.model,
    session_id: params.sessionId,
    days: params.days,
  })
}

export function createDemoTrace() {
  return request<TraceRead>('/api/v1/demo/trace', undefined, { method: 'POST' }).catch(
    async (error: unknown) => {
      const message = error instanceof Error ? error.message : ''
      if (!message.includes('404') && !message.includes('Not Found')) {
        throw error
      }

      return request<TraceRead>('/api/v1/traces', undefined, {
        method: 'POST',
        body: buildFallbackDemoTracePayload(),
      })
    },
  )
}

function buildFallbackDemoTracePayload() {
  const variants = [
    { provider: 'openai', model: 'gpt-5.4' },
    { provider: 'anthropic', model: 'claude-sonnet-4-6' },
    { provider: 'gemini', model: 'gemini-2.5-pro' },
  ] as const
  const statuses = ['success', 'success', 'success', 'timeout', 'rate_limit'] as const

  const variant = variants[Math.floor(Math.random() * variants.length)]
  const status = statuses[Math.floor(Math.random() * statuses.length)]
  const sessionId = `demo-session-${Math.floor(Math.random() * 5) + 1}`
  const promptTokens = Math.floor(Math.random() * 1200) + 120
  const completionTokens = status === 'success' ? Math.floor(Math.random() * 280) + 40 : 0

  return {
    trace_id: `demo-${variant.provider}-${crypto.randomUUID()}`,
    session_id: sessionId,
    user_id: 'demo-user',
    provider: variant.provider,
    model: variant.model,
    endpoint: 'demo.synthetic.generate',
    request: {
      messages: [{ role: 'user', content: 'Show me a demo trace' }],
      temperature: Number((0.2 + Math.random() * 0.8).toFixed(2)),
    },
    response:
      status === 'success' ? { content: 'Synthetic response from the dashboard fallback demo.' } : null,
    metadata: { session_id: sessionId, source: 'dashboard-fallback-demo' },
    prompt_tokens: promptTokens,
    completion_tokens: completionTokens,
    latency_ms: Math.floor(Math.random() * 3000) + 180,
    status,
    error_msg:
      status === 'timeout' ? 'request timeout' : status === 'rate_limit' ? 'rate limit exceeded' : null,
    timestamp: new Date().toISOString(),
  }
}
