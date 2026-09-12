import { cn } from '@/lib/utils'
import type { NextAction } from '@/lib/types'
import {
  AlertCircle,
  Clock,
  Calendar,
  Send,
  FileText,
  Users,
  TrendingUp,
  CheckCircle2,
} from 'lucide-react'

const urgencyConfig = {
  urgent: { bg: 'bg-accent-rose/10', text: 'text-accent-rose', label: 'Urgent', icon: <AlertCircle size={14} /> },
  today: { bg: 'bg-accent-amber/10', text: 'text-accent-amber', label: 'Today', icon: <Clock size={14} /> },
  'this-week': { bg: 'bg-accent-cyan/10', text: 'text-accent-cyan', label: 'This Week', icon: <Calendar size={14} /> },
  someday: { bg: 'bg-slate-500/10', text: 'text-slate-400', label: 'Someday', icon: <Calendar size={14} /> },
}

const actionIcon = {
  'follow-up': <Send size={16} />,
  apply: <FileText size={16} />,
  prep: <CheckCircle2 size={16} />,
  negotiate: <TrendingUp size={16} />,
  network: <Users size={16} />,
}

export function NextActionCard({ action, onClick }: { action: NextAction; onClick?: () => void }) {
  const urgency = urgencyConfig[action.urgency]

  return (
    <div
      onClick={onClick}
      className={cn(
        'flex items-start gap-3 p-3.5 rounded-xl border border-border-subtle bg-bg-surface',
        'transition-all duration-150 hover:border-border hover:bg-bg-surface2 cursor-pointer',
      )}
    >
      <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center shrink-0', urgency.bg, urgency.text)}>
        {actionIcon[action.actionType]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <h4 className="text-sm font-semibold text-text-primary truncate">{action.title}</h4>
        </div>
        <p className="text-xs text-text-secondary line-clamp-2">{action.description}</p>
        <div className="flex items-center gap-2 mt-2">
          <span className={cn('badge text-2xs', urgency.bg, urgency.text)}>
            {urgency.icon}
            {urgency.label}
          </span>
          {action.company && (
            <span className="text-2xs text-text-muted font-medium">{action.company}</span>
          )}
        </div>
      </div>
    </div>
  )
}
