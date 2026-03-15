import { useEffect, useRef, useState } from 'react'

import { TRACE_STREAM_URL } from '../lib/api'
import type { TraceRead, TraceStreamMessage } from '../lib/types'

export type TraceStreamStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export function useTraceStream(onTrace: (trace: TraceRead) => void) {
  const onTraceRef = useRef(onTrace)
  const [status, setStatus] = useState<TraceStreamStatus>('connecting')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    onTraceRef.current = onTrace
  }, [onTrace])

  useEffect(() => {
    let socket: WebSocket | null = null
    let reconnectTimer: number | null = null
    let disposed = false

    const connect = () => {
      setStatus('connecting')
      socket = new WebSocket(TRACE_STREAM_URL)

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as TraceStreamMessage
          if (payload.event === 'connected') {
            setStatus('connected')
            setError(null)
            return
          }

          if (payload.event === 'trace.created') {
            onTraceRef.current(payload.data as TraceRead)
          }
        } catch {
          setStatus('error')
          setError('Received malformed data from the trace stream')
        }
      }

      socket.onerror = () => {
        setStatus('error')
        setError('Unable to reach the live trace stream')
      }

      socket.onclose = () => {
        if (disposed) {
          setStatus('disconnected')
          return
        }

        setStatus('disconnected')
        reconnectTimer = window.setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      disposed = true
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer)
      }
      socket?.close()
    }
  }, [])

  return { status, error }
}
