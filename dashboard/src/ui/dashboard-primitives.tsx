import type { ReactNode } from 'react'

export function SectionHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-3">
        <p className="eyebrow">{eyebrow}</p>
        <div className="space-y-2">
          <h2 className="text-3xl font-extrabold tracking-tight text-text sm:text-5xl">{title}</h2>
          <p className="max-w-2xl text-sm leading-7 text-muted sm:text-base">{description}</p>
        </div>
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  )
}

export function MetricCard({
  label,
  value,
  trend,
}: {
  label: string
  value: string
  trend: string
}) {
  return (
    <div className="panel-card-soft p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <p className="metric-label">{label}</p>
      <p className="metric-value mt-4">{value}</p>
      <p className="mt-3 text-sm text-muted">{trend}</p>
    </div>
  )
}

export function PlaceholderPanel({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle: string
  children: ReactNode
}) {
  return (
    <section className="panel-card p-5 sm:p-6 lg:p-7">
      <div className="mb-6 space-y-2">
        <h3 className="text-xl font-bold tracking-tight text-text">{title}</h3>
        <p className="text-sm leading-6 text-muted">{subtitle}</p>
      </div>
      {children}
    </section>
  )
}

export function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div className="rounded-2xl border border-dashed border-white/15 bg-white/5 px-6 py-10 text-center">
      <p className="text-sm font-medium text-text">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">{description}</p>
    </div>
  )
}

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-8 text-sm text-muted">
      {label}
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-rose/25 bg-rose/10 px-6 py-8 text-sm text-rose">
      {message}
    </div>
  )
}
