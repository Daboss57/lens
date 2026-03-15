import { useCallback, useState } from 'react'

import { createDemoTrace } from '../lib/api'
import type { TraceRead } from '../lib/types'

export function useCreateDemoTrace() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastTrace, setLastTrace] = useState<TraceRead | null>(null)

  const trigger = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const trace = await createDemoTrace()
      setLastTrace(trace)
      return trace
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to create demo trace'
      setError(message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { trigger, loading, error, lastTrace }
}
