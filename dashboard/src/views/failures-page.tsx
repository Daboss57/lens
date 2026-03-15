import { ShieldAlert, TimerReset } from 'lucide-react'

import { useFailureStats } from '../hooks/use-failure-stats'
import { formatDateTime, formatProvider, formatStatus } from '../lib/format'
import { EmptyState, ErrorState, LoadingState, MetricCard, PlaceholderPanel, SectionHeader } from '../ui/dashboard-primitives'
import { StatusChip } from '../ui/status-chip'

export function FailuresPage() {
  const failures = useFailureStats(25)
  const topFailureType = failures.data.by_error_type[0]
  const topProvider = failures.data.by_provider[0]
  const recoveryRate = failures.data.total_failures === 0 ? 100 : 0

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Reliability"
        title="Failures and error drift"
        description="Recent failures, grouped causes, and provider concentration now come directly from the backend failure stats route."
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Failures tracked"
          value={failures.data.total_failures.toString()}
          trend="Rolling view from GET /api/v1/stats/failures"
        />
        <MetricCard
          label="Top failure source"
          value={topFailureType ? formatStatus(topFailureType.key) : 'none'}
          trend={topFailureType ? `${topFailureType.count} matching traces` : 'No failure activity'}
        />
        <MetricCard
          label="Failure pressure"
          value={topProvider ? formatProvider(topProvider.key) : 'none'}
          trend={topProvider ? `${topProvider.count} failed traces` : `${recoveryRate}% clear`}
        />
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <PlaceholderPanel
          title="Recent failure queue"
          subtitle="Backed by GET /api/v1/stats/failures and ready to link into replay views."
        >
          {failures.loading ? <LoadingState label="Loading recent failures..." /> : null}
          {!failures.loading && failures.error ? <ErrorState message={failures.error} /> : null}
          {!failures.loading && !failures.error && failures.data.recent_failures.length === 0 ? (
            <EmptyState
              title="No failures yet"
              description="Once the backend records timeout, rate-limit, empty-response, or error traces, they will appear here."
            />
          ) : null}
          {!failures.loading && !failures.error && failures.data.recent_failures.length > 0 ? (
            <div className="space-y-4">
              {failures.data.recent_failures.map((trace) => (
                <div key={trace.trace_id} className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-medium text-text">{trace.model}</p>
                      <p className="mt-1 text-xs text-muted">
                        {formatProvider(trace.provider)} · {formatDateTime(trace.timestamp)}
                      </p>
                    </div>
                    <StatusChip label={formatStatus(trace.status)} tone="danger" />
                  </div>
                  {trace.error_msg ? (
                    <p className="mt-3 text-sm leading-6 text-muted">{trace.error_msg}</p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
        </PlaceholderPanel>

        <PlaceholderPanel
          title="Escalation view"
          subtitle="Grouped provider and error-type breakdowns for quick triage."
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <ShieldAlert className="h-5 w-5 text-rose" />
              <p className="mt-4 text-sm font-medium text-text">Error taxonomy</p>
              <div className="mt-3 space-y-2 text-sm text-muted">
                {failures.data.by_error_type.length === 0 ? (
                  <p>No classified failures yet.</p>
                ) : (
                  failures.data.by_error_type.map((bucket) => (
                    <div key={bucket.key} className="flex items-center justify-between gap-4">
                      <span>{formatStatus(bucket.key)}</span>
                      <span className="font-mono text-xs text-text">{bucket.count}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <TimerReset className="h-5 w-5 text-signal" />
              <p className="mt-4 text-sm font-medium text-text">Provider spread</p>
              <div className="mt-3 space-y-2 text-sm text-muted">
                {failures.data.by_provider.length === 0 ? (
                  <p>No provider failures yet.</p>
                ) : (
                  failures.data.by_provider.map((bucket) => (
                    <div key={bucket.key} className="flex items-center justify-between gap-4">
                      <span>{formatProvider(bucket.key)}</span>
                      <span className="font-mono text-xs text-text">{bucket.count}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </PlaceholderPanel>
      </div>
    </div>
  )
}
