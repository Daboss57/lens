import { ArrowUpRight, Filter, Radio, RefreshCcw, Sparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { useCreateDemoTrace } from '../hooks/use-create-demo-trace'
import { useLiveTraces } from '../hooks/use-live-traces'
import { useOverviewStats } from '../hooks/use-overview-stats'
import {
  formatCurrency,
  formatDateTime,
  formatLatency,
  formatProvider,
  formatStatus,
} from '../lib/format'
import type { TraceRead } from '../lib/types'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PlaceholderPanel,
  SectionHeader,
} from '../ui/dashboard-primitives'
import { FilterPill } from '../ui/filter-pill'
import { StatusChip } from '../ui/status-chip'
import { TraceDetailDrawer } from '../ui/trace-detail-drawer'

const providerOptions = [
  { value: 'all', label: 'All providers' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'gemini', label: 'Gemini' },
] as const

const statusOptions = [
  { value: 'all', label: 'All states' },
  { value: 'success', label: 'Success' },
  { value: 'timeout', label: 'Timeouts' },
  { value: 'rate_limit', label: 'Rate limits' },
  { value: 'error', label: 'Errors' },
] as const

export function LiveFeedPage() {
  const overview = useOverviewStats(1)
  const demoTrace = useCreateDemoTrace()
  const [providerFilter, setProviderFilter] = useState<(typeof providerOptions)[number]['value']>('all')
  const [statusFilter, setStatusFilter] = useState<(typeof statusOptions)[number]['value']>('all')
  const [selectedTrace, setSelectedTrace] = useState<TraceRead | null>(null)

  const liveTraces = useLiveTraces({
    provider: providerFilter === 'all' ? undefined : providerFilter,
    status: statusFilter === 'all' ? undefined : statusFilter,
    limit: 50,
  })

  const streamBadgeTone =
    liveTraces.streamStatus === 'connected'
      ? 'border-lime/30 bg-lime/10 text-lime'
      : liveTraces.streamStatus === 'error'
        ? 'border-rose/30 bg-rose/10 text-rose'
        : 'border-highlight/30 bg-highlight/10 text-highlight'

  const latestTraceLabel = useMemo(() => {
    if (!liveTraces.traces[0]) {
      return 'Waiting for traces'
    }
    return `${formatProvider(liveTraces.traces[0].provider)} · ${liveTraces.traces[0].model}`
  }, [liveTraces.traces])

  return (
    <>
      <div className="space-y-6">
        <SectionHeader
          eyebrow="Realtime"
          title="Live trace feed"
          description="A polished pulse view for every model call as it arrives. Filter the stream instantly, inspect any trace, and trigger a local demo without leaving the dashboard."
          action={
            <div className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 font-mono text-xs uppercase tracking-[0.22em] ${streamBadgeTone}`}>
              <Radio className="h-3.5 w-3.5" /> {liveTraces.streamStatus}
            </div>
          }
        />

        <section className="grid gap-4 xl:grid-cols-[1.2fr_1fr_1fr_1fr]">
          <div className="panel-card relative overflow-hidden p-6 xl:col-span-1">
            <div className="absolute inset-0 bg-gradient-to-br from-highlight/12 via-transparent to-indigo-400/10" />
            <div className="relative space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="eyebrow">Live control</p>
                  <h3 className="mt-2 text-2xl font-bold tracking-tight text-text">
                    Fast filtering for the trace stream.
                  </h3>
                </div>
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-highlight/25 bg-highlight/10 text-highlight">
                  <Sparkles className="h-5 w-5" />
                </div>
              </div>

              <div className="space-y-3">
                <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Providers</p>
                <div className="flex flex-wrap gap-2">
                  {providerOptions.map((option) => (
                    <FilterPill
                      key={option.value}
                      active={providerFilter === option.value}
                      icon={<Filter className="h-3.5 w-3.5" />}
                      label={option.label}
                      onClick={() => setProviderFilter(option.value)}
                    />
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">State</p>
                <div className="flex flex-wrap gap-2">
                  {statusOptions.map((option) => (
                    <FilterPill
                      key={option.value}
                      active={statusFilter === option.value}
                      label={option.label}
                      onClick={() => setStatusFilter(option.value)}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Latest trace</p>
                    <p className="mt-2 text-sm font-medium text-text">{latestTraceLabel}</p>
                  </div>
                  <button
                    className="rounded-full border border-highlight/30 bg-highlight/10 px-4 py-2 text-sm font-medium text-highlight transition hover:bg-highlight/15"
                    onClick={() => {
                      void demoTrace.trigger()
                    }}
                    type="button"
                  >
                    {demoTrace.loading ? 'Seeding...' : 'Seed demo'}
                  </button>
                </div>
                {demoTrace.error ? <p className="mt-3 text-xs text-rose">{demoTrace.error}</p> : null}
              </div>
            </div>
          </div>

          <MetricCard
            label="Traces today"
            value={overview.loading ? '...' : overview.data.total_traces.toString()}
            trend="Fresh from GET /api/v1/stats/overview over the last 24 hours"
          />
          <MetricCard
            label="Failures today"
            value={overview.loading ? '...' : overview.data.failed_traces.toString()}
            trend="Useful early signal before drilling into the failure workspace"
          />
          <MetricCard
            label="Avg latency"
            value={overview.loading ? '...' : formatLatency(overview.data.average_latency_ms)}
            trend={`Total spend today: ${formatCurrency(overview.data.total_cost_usd)}`}
          />
        </section>

        <div className="grid gap-6 xl:grid-cols-[1.6fr_0.9fr]">
          <PlaceholderPanel
            title="Incoming traces"
            subtitle="Newest traces are prepended live. Filters reload the backend snapshot so you can pivot quickly without losing the stream. Select any row for a full request/response inspection."
          >
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-3 text-xs uppercase tracking-[0.18em] text-muted">
                <StatusChip label="50 trace window" tone="neutral" />
                <StatusChip label="websocket + rest" tone="info" />
              </div>
              <button
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-muted transition hover:border-highlight/30 hover:text-text"
                onClick={liveTraces.refresh}
                type="button"
              >
                <RefreshCcw className="h-3.5 w-3.5" /> Refresh
              </button>
            </div>

            {liveTraces.loading ? <LoadingState label="Loading recent traces..." /> : null}
            {!liveTraces.loading && liveTraces.error ? <ErrorState message={liveTraces.error} /> : null}
            {!liveTraces.loading && !liveTraces.error && liveTraces.traces.length === 0 ? (
              <EmptyState
                title="No traces yet"
                description="Start your app with a patched SDK client or hit the Seed demo button and traces will appear here immediately."
              />
            ) : null}

            {!liveTraces.loading && !liveTraces.error && liveTraces.traces.length > 0 ? (
              <div className="overflow-hidden rounded-2xl border border-white/10">
                <table className="min-w-full border-collapse text-left text-sm">
                  <thead className="bg-white/5 text-muted">
                    <tr>
                      <th className="px-4 py-3 font-medium">Trace</th>
                      <th className="px-4 py-3 font-medium">Provider</th>
                      <th className="px-4 py-3 font-medium">Model</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Latency</th>
                      <th className="px-4 py-3 font-medium">Cost</th>
                      <th className="px-4 py-3 font-medium">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {liveTraces.traces.map((trace) => (
                      <tr
                        key={trace.trace_id}
                        className="table-row-hover cursor-pointer border-t border-white/10 align-top"
                        onClick={() => setSelectedTrace(trace)}
                      >
                        <td className="px-4 py-4 font-mono text-[11px] text-muted">{trace.trace_id.slice(0, 8)}</td>
                        <td className="px-4 py-4 text-text">{formatProvider(trace.provider)}</td>
                        <td className="px-4 py-4 font-mono text-xs text-muted">{trace.model}</td>
                        <td className="px-4 py-4">
                          <StatusChip
                            label={formatStatus(trace.status)}
                            tone={trace.status === 'success' ? 'success' : 'danger'}
                          />
                        </td>
                        <td className="px-4 py-4 text-muted">{formatLatency(trace.latency_ms)}</td>
                        <td className="px-4 py-4 text-text">{formatCurrency(trace.cost_usd)}</td>
                        <td className="px-4 py-4 text-muted">{formatDateTime(trace.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </PlaceholderPanel>

          <PlaceholderPanel
            title="Operator notes"
            subtitle="High-level control info from the live feed, including backend stream state, provider activity, and the local demo entrypoint."
          >
            <div className="space-y-4 text-sm text-muted">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-medium text-text">WebSocket state</p>
                <p className="mt-2">
                  {liveTraces.streamError ?? 'The live trace stream is connected and ready to prepend new events.'}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-medium text-text">Active providers</p>
                <div className="mt-3 space-y-2">
                  {overview.data.providers.length === 0 ? (
                    <p>No provider activity yet.</p>
                  ) : (
                    overview.data.providers.map((provider) => (
                      <div key={provider.provider} className="flex items-center justify-between gap-4">
                        <span>{formatProvider(provider.provider)}</span>
                        <span className="font-mono text-xs text-highlight">{provider.trace_count} traces</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-medium text-text">One-click demo</p>
                <p className="mt-2 leading-6">
                  The Seed demo button calls the backend demo endpoint and broadcasts the new trace into the live stream instantly.
                </p>
              </div>
              <Link className="inline-flex items-center gap-2 text-sm font-medium text-highlight" to="/sessions">
                Jump to replay shell <ArrowUpRight className="h-4 w-4" />
              </Link>
            </div>
          </PlaceholderPanel>
        </div>
      </div>

      <TraceDetailDrawer trace={selectedTrace} onClose={() => setSelectedTrace(null)} />
    </>
  )
}
