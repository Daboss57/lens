import { useCallback } from 'react'

import { getCosts } from '../lib/api'
import type { CostsResponse } from '../lib/types'
import { useApiQuery } from './use-api-query'

export function useCostBuckets(params: {
  groupBy: 'day' | 'provider' | 'model'
  provider?: string
  model?: string
  sessionId?: string
  days?: number
}) {
  const key = JSON.stringify(params)
  const fetcher = useCallback(() => getCosts(params), [key])
  return useApiQuery<CostsResponse>(fetcher, [key], {
    initialData: { group_by: params.groupBy, buckets: [] },
  })
}
