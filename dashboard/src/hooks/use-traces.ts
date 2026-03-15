import { useCallback } from 'react'

import { getTraces } from '../lib/api'
import type { TraceRead } from '../lib/types'
import { useApiQuery } from './use-api-query'

export function useTraces(params?: {
  provider?: string
  model?: string
  status?: string
  sessionId?: string
  days?: number
  limit?: number
  offset?: number
}) {
  const key = JSON.stringify(params ?? {})
  const fetcher = useCallback(() => getTraces(params), [key])
  return useApiQuery<TraceRead[]>(fetcher, [key], { initialData: [] })
}
