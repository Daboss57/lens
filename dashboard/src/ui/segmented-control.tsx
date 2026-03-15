interface SegmentedOption<T extends string> {
  value: T
  label: string
}

interface SegmentedControlProps<T extends string> {
  value: T
  onChange: (value: T) => void
  options: Array<SegmentedOption<T>>
}

export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
}: SegmentedControlProps<T>) {
  return (
    <div className="inline-flex rounded-full border border-white/10 bg-white/5 p-1">
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            className={[
              'rounded-full px-3 py-2 text-xs font-medium transition sm:px-4',
              active ? 'bg-text text-ink shadow-sm' : 'text-muted hover:text-text',
            ].join(' ')}
            onClick={() => onChange(option.value)}
            type="button"
          >
            {option.label}
          </button>
        )}
      )}
    </div>
  )
}
