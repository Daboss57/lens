import { useCallback, useEffect, useMemo, useState } from 'react'

type SetStateAction<T> = T | ((current: T) => T)

export function useApiQuery<T>(
  fetcher: () => Promise<T>,
  dependencies: readonly unknown[],
  options: { enabled?: boolean; initialData: T },
) {
  const enabled = options?.enabled ?? true
  const [data, setData] = useState<T>(options.initialData)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    if (!enabled) {
      setLoading(false)
      return
    }

    let active = true
    setLoading(true)
    setError(null)

    fetcher()
      .then((result) => {
        if (!active) {
          return
        }
        setData(result)
      })
      .catch((fetchError: unknown) => {
        if (!active) {
          return
        }
        setError(fetchError instanceof Error ? fetchError.message : 'Request failed')
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [enabled, reloadToken, fetcher, ...dependencies])

  const refresh = useCallback(() => {
    setReloadToken((current) => current + 1)
  }, [])

  const updateData = useCallback((nextValue: SetStateAction<T>) => {
    setData((current) =>
      typeof nextValue === 'function'
        ? (nextValue as (current: T) => T)(current)
        : nextValue,
    )
  }, [])

  return useMemo(
    () => ({ data, setData: updateData, loading, error, refresh }),
    [data, error, loading, refresh, updateData],
  )
}
