import { useCallback } from 'react'

import { getOverviewStats } from '../lib/api'
import type { OverviewStats } from '../lib/types'
import { useApiQuery } from './use-api-query'

const initialData: OverviewStats = {
  total_traces: 0,
  successful_traces: 0,
  failed_traces: 0,
  total_cost_usd: 0,
  average_latency_ms: 0,
  providers: [],
}

export function useOverviewStats(days?: number) {
  const fetcher = useCallback(() => getOverviewStats(days), [days])
  return useApiQuery(fetcher, [days], { initialData })
}
