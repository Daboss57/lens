import { Activity, AlertTriangle, Coins, Layers3, PlayCircle, Sparkles } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { useHealth } from '../hooks/use-health'
import { StatusChip } from './status-chip'

const navigation = [
  { to: '/', label: 'Live Feed', icon: Activity, kicker: 'Realtime trace stream' },
  { to: '/costs', label: 'Cost Tracker', icon: Coins, kicker: 'Spend and burn rate' },
  { to: '/failures', label: 'Failures', icon: AlertTriangle, kicker: 'Error pressure and drift' },
  { to: '/sessions', label: 'Sessions', icon: Layers3, kicker: 'Replay and sequencing' },
  { to: '/demo', label: 'Demo Flow', icon: PlayCircle, kicker: 'Seed local traces fast' },
]

export function AppShell() {
  const health = useHealth()
  const apiReady = health.data.status === 'ok' && !health.error
  const location = useLocation()

  return (
    <div className="relative min-h-screen overflow-hidden text-text">
      <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:28px_28px] opacity-20" />
      <div className="pointer-events-none absolute -left-24 top-10 h-72 w-72 rounded-full bg-cyan-400/15 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-0 h-80 w-80 rounded-full bg-indigo-500/15 blur-3xl" />
      <div className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-6 px-4 py-4 sm:px-6 lg:px-8 lg:py-8">
        <header className="glass-strip flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-highlight/35 bg-gradient-to-br from-highlight/20 to-indigo-400/10 text-highlight shadow-[0_12px_30px_rgba(56,189,248,0.18)]">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="eyebrow">LENS Control Surface</p>
              <h1 className="text-xl font-extrabold tracking-tight sm:text-2xl">
                Local observability for model calls.
              </h1>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <StatusChip label={apiReady ? 'API online' : health.loading ? 'checking api' : 'API offline'} tone={apiReady ? 'success' : 'warning'} />
            <div className="glass-strip px-4 py-2 text-right">
              <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">Target</p>
              <p className="text-sm text-text">http://localhost:8100</p>
            </div>
          </div>
        </header>

        <div className="grid flex-1 gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="panel-card flex flex-col gap-6 p-5 sm:p-6">
            <div className="space-y-3">
              <p className="eyebrow">Workspace</p>
              <p className="text-sm leading-6 text-muted">
                A sleeker command center for live traces, spend, failures, and replay. Everything here is tuned for fast scanning and low friction.
              </p>
            </div>

            <nav className="grid gap-3">
              {navigation.map(({ to, label, icon: Icon, kicker }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    [
                      'group rounded-[1.5rem] border p-4 transition duration-200',
                      isActive
                        ? 'border-white/12 bg-gradient-to-br from-white/10 to-highlight/10 shadow-[0_18px_44px_rgba(7,11,23,0.32)]'
                        : 'border-white/8 bg-white/[0.03] hover:border-white/15 hover:bg-white/[0.05]',
                    ].join(' ')
                  }
                >
                  {({ isActive }) => (
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex gap-3">
                        <div
                          className={[
                            'mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl border',
                            isActive
                              ? 'border-highlight/30 bg-highlight/10 text-highlight'
                              : 'border-white/10 bg-white/5 text-muted',
                          ].join(' ')}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-text">{label}</p>
                          <p className="mt-1 text-xs leading-5 text-muted">{kicker}</p>
                        </div>
                      </div>
                      <span className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted">
                        {location.pathname === to ? 'open' : 'view'}
                      </span>
                    </div>
                  )}
                </NavLink>
              ))}
            </nav>

            <div className="panel-card-soft p-4">
              <p className="eyebrow">Connection</p>
              <div className="mt-3 space-y-3 text-sm text-muted">
                <div className="flex items-center justify-between gap-4">
                  <span>Backend health</span>
                  <StatusChip label={apiReady ? 'healthy' : 'retrying'} tone={apiReady ? 'success' : 'warning'} />
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Database path</span>
                  <span className="max-w-[10rem] truncate font-mono text-xs text-text">
                    {health.data.database_path || 'pending'}
                  </span>
                </div>
                {health.error ? <p className="text-xs text-signal">{health.error}</p> : null}
              </div>
            </div>
          </aside>

          <main className="min-w-0 py-1">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
