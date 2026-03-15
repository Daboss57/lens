interface StatusChipProps {
  label: string
  tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info'
}

const toneClasses: Record<NonNullable<StatusChipProps['tone']>, string> = {
  neutral: 'border-white/10 bg-white/5 text-muted',
  success: 'border-lime/30 bg-lime/10 text-lime',
  warning: 'border-signal/30 bg-signal/10 text-signal',
  danger: 'border-rose/30 bg-rose/10 text-rose',
  info: 'border-highlight/30 bg-highlight/10 text-highlight',
}

export function StatusChip({ label, tone = 'neutral' }: StatusChipProps) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-3 py-1 font-mono text-[11px] uppercase tracking-[0.22em]',
        toneClasses[tone],
      ].join(' ')}
    >
      {label}
    </span>
  )
}
