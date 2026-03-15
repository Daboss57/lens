import { useCallback } from 'react'

import { getFailureStats } from '../lib/api'
import type { FailureStats } from '../lib/types'
import { useApiQuery } from './use-api-query'

const initialData: FailureStats = {
  total_failures: 0,
  by_error_type: [],
  by_provider: [],
  recent_failures: [],
}

export function useFailureStats(limit = 25) {
  const fetcher = useCallback(() => getFailureStats(limit), [limit])
  return useApiQuery(fetcher, [limit], { initialData })
}
