import { MessagesSquare, Orbit, Waypoints } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { useSessionDetail, useSessions } from '../hooks/use-sessions'
import { formatCurrency, formatDateTime, formatLatency, formatProvider, formatStatus } from '../lib/format'
import type { ReplayStep } from '../lib/types'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PlaceholderPanel,
  SectionHeader,
} from '../ui/dashboard-primitives'
import { SegmentedControl } from '../ui/segmented-control'
import { StatusChip } from '../ui/status-chip'

export function SessionsPage() {
  const sessions = useSessions(50)
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'timeline' | 'compact'>('timeline')

  useEffect(() => {
    if (!selectedSessionId && sessions.data[0]?.session_id) {
      setSelectedSessionId(sessions.data[0].session_id)
    }
  }, [selectedSessionId, sessions.data])

  const sessionDetail = useSessionDetail(selectedSessionId)
  const selectedSession = useMemo(
    () => sessions.data.find((session) => session.session_id === selectedSessionId) ?? null,
    [selectedSessionId, sessions.data],
  )
  const replaySteps = useMemo<ReplayStep[]>(() => {
    if (!sessionDetail.data) {
      return []
    }

    return sessionDetail.data.traces.map((trace) => ({
      trace,
      requestPreview: summarizePayload(trace.request),
      responsePreview: summarizePayload(trace.response ?? { error: trace.error_msg ?? 'No response' }),
      hasError: trace.status !== 'success',
    }))
  }, [sessionDetail.data])

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Replay"
        title="Sessions and turn-by-turn replay"
        description="Select any grouped session, inspect its spend and failures, and replay the trace sequence in time order."
        action={
          <SegmentedControl
            value={viewMode}
            onChange={setViewMode}
            options={[
              { value: 'timeline', label: 'Timeline' },
              { value: 'compact', label: 'Compact' },
            ]}
          />
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Tracked sessions"
          value={sessions.data.length.toString()}
          trend="Current window from GET /api/v1/sessions"
        />
        <MetricCard
          label="Selected session"
          value={selectedSessionId ?? 'none'}
          trend="Choose any session from the directory to update replay detail"
        />
        <MetricCard
          label="Replay cost"
          value={sessionDetail.data ? formatCurrency(sessionDetail.data.session.total_cost_usd) : '$0.00'}
          trend="Spend for the currently selected session"
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <PlaceholderPanel
          title="Session directory"
          subtitle="Choose a session to drive the replay canvas. The directory uses real session summaries from the backend."
        >
          {sessions.loading ? <LoadingState label="Loading sessions..." /> : null}
          {!sessions.loading && sessions.error ? <ErrorState message={sessions.error} /> : null}
          {!sessions.loading && !sessions.error && sessions.data.length === 0 ? (
            <EmptyState
              title="No sessions yet"
              description="Once traces include `session_id`, grouped conversations will appear here automatically."
            />
          ) : null}
          {!sessions.loading && !sessions.error && sessions.data.length > 0 ? (
            <div className="space-y-3">
              {sessions.data.map((session) => {
                const active = selectedSessionId === session.session_id

                return (
                  <button
                    key={session.session_id}
                    className={[
                      'w-full rounded-[1.5rem] border p-4 text-left transition',
                      active
                        ? 'border-highlight/30 bg-highlight/10 shadow-[0_18px_40px_rgba(7,11,23,0.25)]'
                        : 'border-white/10 bg-white/5 hover:border-white/15 hover:bg-white/[0.07]',
                    ].join(' ')}
                    onClick={() => setSelectedSessionId(session.session_id)}
                    type="button"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-sm font-semibold text-text">{session.session_id}</p>
                        <p className="mt-1 text-xs text-muted">Last seen {formatDateTime(session.last_seen_at)}</p>
                      </div>
                      <StatusChip label={`${session.trace_count} traces`} tone={active ? 'info' : 'neutral'} />
                    </div>
                    <div className="mt-4 flex flex-wrap gap-3 text-xs text-muted">
                      <span>{session.success_count} success</span>
                      <span>{session.failure_count} failures</span>
                      <span>{formatCurrency(session.total_cost_usd)}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          ) : null}
        </PlaceholderPanel>

        <PlaceholderPanel
          title="Replay canvas"
          subtitle="The selected session is replayed in the exact order returned from GET /api/v1/sessions/{session_id}."
        >
          {sessionDetail.loading ? <LoadingState label="Loading replay detail..." /> : null}
          {!sessionDetail.loading && sessionDetail.error ? <ErrorState message={sessionDetail.error} /> : null}
          {!sessionDetail.loading && !sessionDetail.error && !sessionDetail.data ? (
            <EmptyState
              title="No replay selected"
              description="Pick a session from the directory to inspect its model calls, status changes, and spend."
            />
          ) : null}
          {!sessionDetail.loading && !sessionDetail.error && sessionDetail.data ? (
            <div className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <MessagesSquare className="h-5 w-5 text-highlight" />
                  <p className="mt-4 text-sm font-medium text-text">{sessionDetail.data.traces.length} turns</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <Waypoints className="h-5 w-5 text-signal" />
                  <p className="mt-4 text-sm font-medium text-text">{sessionDetail.data.session.failure_count} failures</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <Orbit className="h-5 w-5 text-lime" />
                  <p className="mt-4 text-sm font-medium text-text">{selectedSession ? formatCurrency(selectedSession.total_cost_usd) : '$0.00'}</p>
                </div>
              </div>

              <div className="space-y-3">
                {replaySteps.map((step, index) => (
                  <div key={step.trace.trace_id} className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-3">
                          <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-muted">
                            Turn {index + 1}
                          </span>
                          <StatusChip
                            label={formatStatus(step.trace.status)}
                            tone={step.trace.status === 'success' ? 'success' : 'danger'}
                          />
                        </div>
                        <p className="text-sm font-semibold text-text">{step.trace.model}</p>
                        <p className="text-xs text-muted">
                          {formatProvider(step.trace.provider)} · {formatDateTime(step.trace.timestamp)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-4 text-xs text-muted">
                        <span>{formatLatency(step.trace.latency_ms)}</span>
                        <span>{formatCurrency(step.trace.cost_usd)}</span>
                        <span>{step.trace.total_tokens} tokens</span>
                      </div>
                    </div>

                    {viewMode === 'compact' ? (
                      <div className="mt-4 grid gap-3 lg:grid-cols-2">
                        <div className="rounded-2xl border border-white/10 bg-ink/60 p-4">
                          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Prompt summary</p>
                          <p className="mt-3 text-sm leading-6 text-text">{step.requestPreview}</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-ink/60 p-4">
                          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Outcome</p>
                          <p className="mt-3 text-sm leading-6 text-text">{step.responsePreview}</p>
                        </div>
                      </div>
                    ) : null}

                    {viewMode === 'timeline' ? (
                      <div className="mt-4 grid gap-3 lg:grid-cols-2">
                        <div className="rounded-2xl border border-white/10 bg-ink/60 p-4">
                          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Request</p>
                          <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6 text-text">
                            {JSON.stringify(step.trace.request, null, 2)}
                          </pre>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-ink/60 p-4">
                          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Response</p>
                          <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6 text-text">
                            {JSON.stringify(step.trace.response ?? { error: step.trace.error_msg }, null, 2)}
                          </pre>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </PlaceholderPanel>
      </div>
    </div>
  )
}

function summarizePayload(payload: unknown) {
  const raw = JSON.stringify(payload)
  if (!raw) {
    return 'No payload captured.'
  }
  return raw.length > 180 ? `${raw.slice(0, 177)}...` : raw
}
