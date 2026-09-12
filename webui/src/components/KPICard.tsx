import { cn } from '@/lib/utils'
import type { KPICard as KPICardType } from '@/lib/types'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const colorMap = {
  indigo: { bg: 'bg-accent-indigo/10', text: 'text-accent-indigo', border: 'border-accent-indigo/20' },
  cyan: { bg: 'bg-accent-cyan/10', text: 'text-accent-cyan', border: 'border-accent-cyan/20' },
  amber: { bg: 'bg-accent-amber/10', text: 'text-accent-amber', border: 'border-accent-amber/20' },
  violet: { bg: 'bg-accent-violet/10', text: 'text-accent-violet', border: 'border-accent-violet/20' },
  rose: { bg: 'bg-accent-rose/10', text: 'text-accent-rose', border: 'border-accent-rose/20' },
  emerald: { bg: 'bg-accent-emerald/10', text: 'text-accent-emerald', border: 'border-accent-emerald/20' },
}

export function KPICard({ kpi }: { kpi: KPICardType }) {
  const c = colorMap[kpi.color]
  const TrendIcon = kpi.trend === 'up' ? TrendingUp : kpi.trend === 'down' ? TrendingDown : Minus

  return (
    <div className={cn('card p-4 border transition-all duration-200 hover:shadow-md hover:shadow-black/30', c.border)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-text-secondary">{kpi.label}</span>
        {kpi.change && (
          <span className={cn('flex items-center gap-1 text-2xs font-semibold', c.text)}>
            <TrendIcon size={12} />
            {kpi.change}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-text-primary">{kpi.value}</span>
      </div>
    </div>
  )
}
