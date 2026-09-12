import { useAppStore } from '@/store/useAppStore'
import { Sidebar } from '@/components/Sidebar'
import { Dashboard } from '@/pages/Dashboard'
import { JobAnalysis } from '@/pages/JobAnalysis'
import { ApplicationKit } from '@/pages/ApplicationKit'
import { CoverLetterStudio } from '@/pages/CoverLetterStudio'
import { LinkedInComposer } from '@/pages/LinkedInComposer'
import { InterviewPrep } from '@/pages/InterviewPrep'
import { SalaryCalculator } from '@/pages/SalaryCalculator'
import { Search, Settings } from 'lucide-react'
import { mockProfile, SHOW_MOCK_BADGE } from '@/lib/mockData'
import { dataService, type DataSource } from '@/lib/dataService'
import { useState, useEffect } from 'react'

const dataSourceLabel: Record<string, string> = {
  'mock': 'Demo Data',
  'excel-readonly': 'Excel Read-Only',
  'fallback': 'Fallback',
}
const dataSourceColor: Record<string, string> = {
  'mock': 'text-text-muted bg-bg-surface2 border-border-subtle',
  'excel-readonly': 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50',
  'fallback': 'text-amber-400 bg-amber-950/40 border-amber-800/50',
}

const pageTitles: Record<string, string> = {
  dashboard: 'Dashboard',
  'job-analysis': 'Job Analysis',
  'application-kit': 'Application Kit',
  'cover-letter': 'Cover Letter Studio',
  linkedin: 'LinkedIn Composer',
  'interview-prep': 'Interview Prep',
  'salary-calc': 'Salary Calculator',
}

export default function App() {
  const { currentPage } = useAppStore()
  const [dataSource, setDataSource] = useState<DataSource>(dataService.getDataSource())

  useEffect(() => {
    const unsub = dataService.onSourceChange((source) => setDataSource(source))
    return unsub
  }, [])

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'job-analysis':
        return <JobAnalysis />
      case 'application-kit':
        return <ApplicationKit />
      case 'cover-letter':
        return <CoverLetterStudio />
      case 'linkedin':
        return <LinkedInComposer />
      case 'interview-prep':
        return <InterviewPrep />
      case 'salary-calc':
        return <SalaryCalculator />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top command bar */}
        <header className="h-14 border-b border-border-subtle bg-bg-sidebar flex items-center justify-between px-4 lg:px-6 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-text-primary">{pageTitles[currentPage]}</h2>
            {SHOW_MOCK_BADGE && dataSource === 'mock' && (
              <span className="text-2xs text-text-muted bg-bg-surface2 px-2 py-0.5 rounded-full border border-border-subtle">Live Demo (Mock Data)</span>
            )}
            <span className={`text-2xs px-2 py-0.5 rounded-full border ${dataSourceColor[dataSource]}`}>
              Data: {dataSourceLabel[dataSource]}
            </span>
          </div>

          <div className="flex items-center gap-2 lg:gap-3">
            <div className="relative hidden sm:block">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                placeholder="Search..."
                className="bg-bg-surface2 border border-border-subtle rounded-lg pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-indigo w-32 lg:w-48 transition-all"
              />
            </div>
            <button className="p-2 rounded-lg text-text-muted hover:bg-bg-surface2 hover:text-text-primary transition-colors">
              <Settings size={17} />
            </button>
            <div className="w-px h-6 bg-border-subtle" />
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-indigo to-accent-violet flex items-center justify-center text-white text-xs font-bold">
                {mockProfile.initials}
              </div>
              <div className="hidden md:flex flex-col">
                <span className="text-xs font-semibold text-text-primary">{mockProfile.name}</span>
                <span className="text-2xs text-text-muted">{mockProfile.status}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}
