import { CalendarRange, Wallet } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { useCostBuckets } from '../hooks/use-cost-buckets'
import { useOverviewStats } from '../hooks/use-overview-stats'
import { formatCurrency, formatDayLabel, formatProvider } from '../lib/format'
import { EmptyState, ErrorState, LoadingState, MetricCard, PlaceholderPanel, SectionHeader } from '../ui/dashboard-primitives'
import { StatusChip } from '../ui/status-chip'

export function CostTrackerPage() {
  const overview = useOverviewStats(7)
  const dailyCosts = useCostBuckets({ groupBy: 'day', days: 7 })
  const providerCosts = useCostBuckets({ groupBy: 'provider', days: 7 })

  const topProvider = providerCosts.data.buckets[0]
  const topModelCost = dailyCosts.data.buckets.reduce((sum, bucket) => sum + bucket.cost_usd, 0)

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Finance"
        title="Cost tracker"
        description="Daily spend, provider mix, and trend movement are now driven by the backend stats endpoints."
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="7 day spend"
          value={formatCurrency(overview.data.total_cost_usd)}
          trend="Computed from GET /api/v1/stats/overview"
        />
        <MetricCard
          label="Top provider"
          value={topProvider ? formatProvider(topProvider.key) : '—'}
          trend={topProvider ? formatCurrency(topProvider.cost_usd) : 'Waiting for trace data'}
        />
        <MetricCard
          label="Daily average"
          value={formatCurrency(topModelCost / Math.max(dailyCosts.data.buckets.length, 1))}
          trend="Based on the current 7 day window"
        />
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <PlaceholderPanel
          title="Spend contour"
          subtitle="Seven-day spend curve using `/api/v1/stats/costs?group_by=day`."
        >
          <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-ink/80 p-6">
            <div className="absolute inset-0 bg-gradient-to-br from-highlight/10 via-transparent to-signal/10" />
            <div className="relative grid gap-6 md:grid-cols-[0.9fr_1.1fr]">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs uppercase tracking-[0.2em] text-muted">
                  <CalendarRange className="h-4 w-4" /> last 7 days
                </div>
                <p className="text-4xl font-bold tracking-tight text-text">
                  {formatCurrency(overview.data.total_cost_usd)}
                </p>
                <p className="max-w-xs text-sm leading-6 text-muted">
                  The curve below updates automatically once traces accumulate on the backend.
                </p>
              </div>

              {dailyCosts.loading ? <LoadingState label="Loading daily cost buckets..." /> : null}
              {!dailyCosts.loading && dailyCosts.error ? <ErrorState message={dailyCosts.error} /> : null}
              {!dailyCosts.loading && !dailyCosts.error && dailyCosts.data.buckets.length === 0 ? (
                <EmptyState
                  title="No cost data yet"
                  description="As soon as traces are ingested and priced, the seven-day spend contour will render here."
                />
              ) : null}
              {!dailyCosts.loading && !dailyCosts.error && dailyCosts.data.buckets.length > 0 ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={dailyCosts.data.buckets.map((bucket) => ({
                        day: formatDayLabel(bucket.key),
                        cost: Number(bucket.cost_usd.toFixed(4)),
                      }))}
                    >
                      <defs>
                        <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#64d2ff" stopOpacity={0.75} />
                          <stop offset="95%" stopColor="#64d2ff" stopOpacity={0.04} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(157, 173, 207, 0.12)" vertical={false} />
                      <XAxis dataKey="day" tick={{ fill: '#9badcf', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: '#9badcf', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: '#111831',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '16px',
                          color: '#e8eefc',
                        }}
                        formatter={(value: number) => formatCurrency(value)}
                      />
                      <Area type="monotone" dataKey="cost" stroke="#64d2ff" strokeWidth={2} fill="url(#costGradient)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : null}
            </div>
          </div>
        </PlaceholderPanel>

        <PlaceholderPanel
          title="Provider share"
          subtitle="Compact provider-level breakdown using `/api/v1/stats/costs?group_by=provider`."
        >
          <div className="space-y-4">
            {providerCosts.loading ? <LoadingState label="Loading provider cost share..." /> : null}
            {!providerCosts.loading && providerCosts.error ? <ErrorState message={providerCosts.error} /> : null}
            {!providerCosts.loading && !providerCosts.error && providerCosts.data.buckets.length === 0 ? (
              <EmptyState
                title="No provider spend yet"
                description="Once traces arrive, each provider cost bucket will show up here."
              />
            ) : null}
            {!providerCosts.loading && !providerCosts.error
              ? providerCosts.data.buckets.map((bucket) => (
                  <div key={bucket.key} className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-sm font-medium text-text">{formatProvider(bucket.key)}</span>
                      <span className="font-mono text-sm text-muted">{formatCurrency(bucket.cost_usd)}</span>
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-4">
                      <p className="text-xs text-muted">{bucket.trace_count} traces in the current window</p>
                      <StatusChip label={`${bucket.trace_count} traces`} tone="neutral" />
                    </div>
                  </div>
                ))
              : null}
            <div className="rounded-2xl border border-highlight/20 bg-highlight/10 p-4 text-sm text-highlight">
              <div className="flex items-center gap-2 font-medium">
                <Wallet className="h-4 w-4" /> Optimization hook
              </div>
              <p className="mt-2 leading-6 text-highlight/80">
                Model-level cost charts can slot in next without changing this page structure.
              </p>
            </div>
          </div>
        </PlaceholderPanel>
      </div>
    </div>
  )
}
