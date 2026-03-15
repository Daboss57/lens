import { X } from 'lucide-react'

import { formatCurrency, formatDateTime, formatLatency, formatProvider, formatStatus } from '../lib/format'
import type { TraceRead } from '../lib/types'
import { StatusChip } from './status-chip'

export function TraceDetailDrawer({
  trace,
  onClose,
}: {
  trace: TraceRead | null
  onClose: () => void
}) {
  if (!trace) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/55 backdrop-blur-sm">
      <button aria-label="Close trace detail" className="flex-1 cursor-default" onClick={onClose} type="button" />
      <aside className="h-full w-full max-w-2xl overflow-y-auto border-l border-white/10 bg-[#0a1120]/95 px-5 py-5 shadow-[0_0_80px_rgba(5,8,18,0.65)] sm:px-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Trace detail</p>
            <h3 className="mt-2 text-2xl font-bold tracking-tight text-text">{trace.model}</h3>
            <p className="mt-2 text-sm text-muted">
              {formatProvider(trace.provider)} · {formatDateTime(trace.timestamp)}
            </p>
          </div>
          <button
            className="rounded-2xl border border-white/10 bg-white/5 p-3 text-muted transition hover:text-text"
            onClick={onClose}
            type="button"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <StatusChip label={formatStatus(trace.status)} tone={trace.status === 'success' ? 'success' : 'danger'} />
          <StatusChip label={trace.trace_id.slice(0, 12)} tone="neutral" />
          <StatusChip label={formatLatency(trace.latency_ms)} tone="info" />
          <StatusChip label={formatCurrency(trace.cost_usd)} tone="warning" />
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Session</p>
            <p className="mt-3 text-sm text-text">{trace.session_id ?? 'none'}</p>
          </div>
          <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Tokens</p>
            <p className="mt-3 text-sm text-text">{trace.total_tokens} total</p>
          </div>
        </div>

        <div className="mt-8 space-y-4">
          <section className="rounded-[1.5rem] border border-white/10 bg-ink/60 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Request</p>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6 text-text">
              {JSON.stringify(trace.request, null, 2)}
            </pre>
          </section>

          <section className="rounded-[1.5rem] border border-white/10 bg-ink/60 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Response</p>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6 text-text">
              {JSON.stringify(trace.response ?? { error: trace.error_msg }, null, 2)}
            </pre>
          </section>
        </div>
      </aside>
    </div>
  )
}
