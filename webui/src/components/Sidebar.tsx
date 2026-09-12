import { useAppStore } from '@/store/useAppStore'
import type { PageId } from '@/lib/types'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FileSearch,
  KanbanSquare,
  PenLine,
  Linkedin,
  MessageSquare,
  Calculator,
  ChevronLeft,
  Zap,
} from 'lucide-react'

const navItems: { id: PageId; label: string; icon: React.ReactNode; badge?: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
  { id: 'job-analysis', label: 'Job Analysis', icon: <FileSearch size={18} /> },
  { id: 'application-kit', label: 'Application Kit', icon: <KanbanSquare size={18} /> },
  { id: 'cover-letter', label: 'Cover Letter', icon: <PenLine size={18} /> },
  { id: 'linkedin', label: 'LinkedIn', icon: <Linkedin size={18} /> },
  { id: 'interview-prep', label: 'Interview Prep', icon: <MessageSquare size={18} /> },
  { id: 'salary-calc', label: 'Salary Calc', icon: <Calculator size={18} /> },
]

export function Sidebar() {
  const { currentPage, setPage, sidebarCollapsed, toggleSidebar } = useAppStore()

  return (
    <aside
      className={cn(
        'flex flex-col bg-bg-sidebar border-r border-border-subtle transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-border-subtle shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-indigo to-accent-violet flex items-center justify-center shrink-0">
          <Zap size={18} className="text-white" />
        </div>
        {!sidebarCollapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold text-text-primary truncate">Aviora</span>
            <span className="text-2xs text-text-muted truncate">AI Career Command Center</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setPage(item.id)}
            className={cn(
              'nav-item w-full',
              currentPage === item.id && 'nav-item-active',
              sidebarCollapsed && 'justify-center px-0',
            )}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!sidebarCollapsed && (
              <>
                <span className="flex-1 text-left truncate">{item.label}</span>
                {item.badge && (
                  <span className="text-2xs font-bold bg-accent-indigo/20 text-accent-indigo px-1.5 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </button>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border-subtle p-2 shrink-0">
        <button
          onClick={toggleSidebar}
          className="nav-item w-full justify-center"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft
            size={18}
            className={cn('transition-transform', sidebarCollapsed && 'rotate-180')}
          />
        </button>
      </div>
    </aside>
  )
}
