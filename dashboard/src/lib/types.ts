export type TraceStatus = 'success' | 'error' | 'timeout' | 'rate_limit' | 'empty_response'

export interface TraceRead {
  trace_id: string
  session_id: string | null
  user_id: string | null
  provider: string
  model: string
  endpoint: string | null
  request: Record<string, unknown>
  response: Record<string, unknown> | null
  metadata: Record<string, unknown> | null
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  cost_usd: number
  latency_ms: number
  status: TraceStatus
  error_type: string | null
  error_msg: string | null
  timestamp: string
}

export interface ReplayStep {
  trace: TraceRead
  requestPreview: string
  responsePreview: string
  hasError: boolean
}

export interface SessionSummary {
  session_id: string
  trace_count: number
  success_count: number
  failure_count: number
  total_cost_usd: number
  started_at: string
  last_seen_at: string
}

export interface SessionDetail {
  session: SessionSummary
  traces: TraceRead[]
}

export interface ProviderOverview {
  provider: string
  trace_count: number
  total_cost_usd: number
}

export interface OverviewStats {
  total_traces: number
  successful_traces: number
  failed_traces: number
  total_cost_usd: number
  average_latency_ms: number
  providers: ProviderOverview[]
}

export interface CostBucket {
  key: string
  trace_count: number
  cost_usd: number
  prompt_tokens: number
  completion_tokens: number
}

export interface CostsResponse {
  group_by: 'day' | 'provider' | 'model'
  buckets: CostBucket[]
}

export interface CountBreakdown {
  key: string
  count: number
}

export interface FailureStats {
  total_failures: number
  by_error_type: CountBreakdown[]
  by_provider: CountBreakdown[]
  recent_failures: TraceRead[]
}

export interface HealthResponse {
  status: string
  database_path: string
}

export interface TraceStreamMessage {
  event: 'connected' | 'trace.created'
  data: unknown
}
