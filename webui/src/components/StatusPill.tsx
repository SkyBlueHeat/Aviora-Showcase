import { cn } from '@/lib/utils'
import type { ApplicationStatus } from '@/lib/types'

const statusConfig: Record<ApplicationStatus, { bg: string; text: string; dot: string }> = {
  Saved: { bg: 'bg-slate-500/15', text: 'text-slate-400', dot: 'bg-slate-400' },
  Applied: { bg: 'bg-accent-indigo/15', text: 'text-accent-indigo', dot: 'bg-accent-indigo' },
  'Phone Screen': { bg: 'bg-accent-cyan/15', text: 'text-accent-cyan', dot: 'bg-accent-cyan' },
  Technical: { bg: 'bg-accent-violet/15', text: 'text-accent-violet', dot: 'bg-accent-violet' },
  Onsite: { bg: 'bg-accent-amber/15', text: 'text-accent-amber', dot: 'bg-accent-amber' },
  Offer: { bg: 'bg-accent-emerald/15', text: 'text-accent-emerald', dot: 'bg-accent-emerald' },
  Rejected: { bg: 'bg-accent-rose/15', text: 'text-accent-rose', dot: 'bg-accent-rose' },
  Ghosted: { bg: 'bg-slate-600/15', text: 'text-slate-500', dot: 'bg-slate-500' },
}

export function StatusPill({ status, size = 'sm' }: { status: ApplicationStatus; size?: 'sm' | 'xs' }) {
  const cfg = statusConfig[status]
  return (
    <span
      className={cn(
        'badge',
        cfg.bg,
        cfg.text,
        size === 'xs' && 'text-2xs px-2 py-0.5',
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', cfg.dot)} />
      {status}
    </span>
  )
}
