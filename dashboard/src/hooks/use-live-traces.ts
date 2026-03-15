import { useCallback, useEffect, useMemo } from 'react'

import type { TraceRead } from '../lib/types'
import { useTraceStream } from './use-trace-stream'
import { useTraces } from './use-traces'

function mergeTraces(incoming: TraceRead[], current: TraceRead[], limit: number) {
  const map = new Map<string, TraceRead>()

  for (const trace of [...incoming, ...current]) {
    map.set(trace.trace_id, trace)
  }

  return [...map.values()]
    .sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp))
    .slice(0, limit)
}

export function useLiveTraces(params?: {
  provider?: string
  status?: string
  limit?: number
}) {
  const limit = params?.limit ?? 50
  const tracesQuery = useTraces({ provider: params?.provider, status: params?.status, limit })

  const handleTrace = useCallback(
    (trace: TraceRead) => {
      tracesQuery.setData((current) => mergeTraces([trace], current, limit))
    },
    [limit, tracesQuery],
  )

  const stream = useTraceStream(handleTrace)
  const traces = useMemo(
    () => [...tracesQuery.data].sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp)),
    [tracesQuery.data],
  )

  return useMemo(
    () => ({
      traces,
      loading: tracesQuery.loading,
      error: tracesQuery.error,
      refresh: tracesQuery.refresh,
      streamStatus: stream.status,
      streamError: stream.error,
    }),
    [stream.error, stream.status, traces, tracesQuery.error, tracesQuery.loading, tracesQuery.refresh],
  )
}
