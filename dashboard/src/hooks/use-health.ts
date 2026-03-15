import { useCallback } from 'react'

import { getHealth } from '../lib/api'
import type { HealthResponse } from '../lib/types'
import { useApiQuery } from './use-api-query'

const initialData: HealthResponse = {
  status: 'unknown',
  database_path: '',
}

export function useHealth() {
  const fetcher = useCallback(() => getHealth(), [])
  return useApiQuery(fetcher, [], { initialData })
}
