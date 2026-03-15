import { PlayCircle, TerminalSquare, Wand2 } from 'lucide-react'

import { useCreateDemoTrace } from '../hooks/use-create-demo-trace'
import { formatDateTime, formatProvider } from '../lib/format'
import { SectionHeader } from '../ui/dashboard-primitives'
import { StatusChip } from '../ui/status-chip'

export function DemoFlowPage() {
  const demoTrace = useCreateDemoTrace()

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Demo"
        title="Local trace demo"
        description="A tiny seeded flow to populate LENS instantly while you develop the product surface."
      />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="panel-card p-6 sm:p-7">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-highlight/25 bg-highlight/10 text-highlight">
              <PlayCircle className="h-5 w-5" />
            </div>
            <div>
              <p className="eyebrow">Quick start</p>
              <h3 className="text-2xl font-bold tracking-tight text-text">Generate traces in seconds</h3>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              className="rounded-full border border-highlight/30 bg-highlight/10 px-5 py-3 text-sm font-medium text-highlight transition hover:bg-highlight/15"
              onClick={() => {
                void demoTrace.trigger()
              }}
              type="button"
            >
              {demoTrace.loading ? 'Generating...' : 'Generate demo trace'}
            </button>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-3 text-sm text-muted">
              or run <code className="font-mono text-xs text-highlight">python scripts/demo_trace.py</code>
            </div>
          </div>

          {demoTrace.error ? <p className="mt-4 text-sm text-rose">{demoTrace.error}</p> : null}

          {demoTrace.lastTrace ? (
            <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-ink/70 p-5">
              <div className="flex flex-wrap items-center gap-3">
                <StatusChip label={formatProvider(demoTrace.lastTrace.provider)} tone="info" />
                <StatusChip label={demoTrace.lastTrace.model} tone="neutral" />
                <StatusChip label={demoTrace.lastTrace.status} tone={demoTrace.lastTrace.status === 'success' ? 'success' : 'danger'} />
              </div>
              <p className="mt-4 text-sm text-muted">
                Last generated at {formatDateTime(demoTrace.lastTrace.timestamp)} for session{' '}
                <span className="font-mono text-xs text-text">{demoTrace.lastTrace.session_id}</span>
              </p>
            </div>
          ) : null}

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <TerminalSquare className="h-5 w-5 text-signal" />
              <p className="mt-4 text-sm font-medium text-text">Writes a trace</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <Wand2 className="h-5 w-5 text-lime" />
              <p className="mt-4 text-sm font-medium text-text">Randomizes provider and outcome</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <PlayCircle className="h-5 w-5 text-highlight" />
              <p className="mt-4 text-sm font-medium text-text">Lights up every dashboard view</p>
            </div>
          </div>
        </section>

        <section className="panel-card p-6 sm:p-7">
          <p className="eyebrow">Flow</p>
          <div className="mt-4 space-y-4 text-sm leading-7 text-muted">
            <p>1. Start the API with <code className="font-mono text-xs text-highlight">python -m lens_server</code>.</p>
            <p>2. Start the dashboard with <code className="font-mono text-xs text-highlight">npm run dev</code> inside <code className="font-mono text-xs text-highlight">dashboard/</code>.</p>
            <p>3. Click <span className="text-text">Generate demo trace</span> or run the script from the terminal.</p>
            <p>4. Watch the live feed, cost tracker, failures page, and sessions replay fill in immediately.</p>
          </div>
        </section>
      </div>
    </div>
  )
}
