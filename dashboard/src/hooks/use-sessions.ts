import { useCallback } from 'react'

import { getSessionDetail, getSessions } from '../lib/api'
import type { SessionDetail, SessionSummary } from '../lib/types'
import { useApiQuery } from './use-api-query'

export function useSessions(limit = 50) {
  const fetcher = useCallback(() => getSessions({ limit }), [limit])
  return useApiQuery<SessionSummary[]>(fetcher, [limit], { initialData: [] })
}

export function useSessionDetail(sessionId: string | null) {
  const fetcher = useCallback(() => getSessionDetail(sessionId ?? ''), [sessionId])
  return useApiQuery<SessionDetail | null>(fetcher, [sessionId], {
    enabled: Boolean(sessionId),
    initialData: null,
  })
}
