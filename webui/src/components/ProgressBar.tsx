import { cn } from '@/lib/utils'

interface ProgressBarProps {
  value: number
  max: number
  label?: string
  color?: string
  showValue?: boolean
}

export function ProgressBar({ value, max, label, color, showValue = true }: ProgressBarProps) {
  const pct = Math.min(100, (value / max) * 100)
  const barColor = color || (pct >= 80 ? 'bg-accent-emerald' : pct >= 50 ? 'bg-accent-cyan' : 'bg-accent-amber')

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && <span className="text-xs font-medium text-text-secondary">{label}</span>}
          {showValue && (
            <span className="text-xs font-semibold text-text-primary">
              {value}/{max}
            </span>
          )}
        </div>
      )}
      <div className="h-2 bg-bg-surface2 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-700 ease-out', barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
