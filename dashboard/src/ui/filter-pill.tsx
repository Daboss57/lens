import type { ReactNode } from 'react'

interface FilterPillProps {
  icon?: ReactNode
  label: string
  active?: boolean
  onClick?: () => void
}

export function FilterPill({ icon, label, active = false, onClick }: FilterPillProps) {
  return (
    <button
      className={[
        'inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition',
        active
          ? 'border-highlight/30 bg-highlight/10 text-text'
          : 'border-white/10 bg-white/5 text-muted hover:border-white/15 hover:text-text',
      ].join(' ')}
      onClick={onClick}
      type="button"
    >
      {icon}
      {label}
    </button>
  )
}
