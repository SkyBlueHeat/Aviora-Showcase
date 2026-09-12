import { useState, useEffect } from 'react'
import { Card, CardHeader } from '@/components/Card'
import { KPICard } from '@/components/KPICard'
import { NextActionCard } from '@/components/NextActionCard'
import { ProgressBar } from '@/components/ProgressBar'
import { ScoreCircle } from '@/components/ScoreCircle'
import { StatusPill } from '@/components/StatusPill'
import {
  mockProfile,
} from '@/lib/mockData'
import { dataService } from '@/lib/dataService'
import type { DataSource } from '@/lib/dataService'
import type { KPICard as KPICardType, Application, NextAction, StreakData } from '@/lib/types'
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import {
  Flame,
  Target,
  TrendingUp,
  Zap,
  ArrowRight,
  Briefcase,
  Calendar,
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'

const SOURCE_COLORS = ['#6366F1', '#22D3EE', '#A78BFA', '#FBBF24']

export function Dashboard() {
  const { setPage } = useAppStore()
  const [kpis, setKpis] = useState<KPICardType[]>([])
  const [monthlyData, setMonthlyData] = useState<{ month: string; applications: number; interviews: number; offers: number }[]>([])
  const [sourceData, setSourceData] = useState<{ source: string; count: number }[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [nextActions, setNextActions] = useState<NextAction[]>([])
  const [streakData, setStreakData] = useState<StreakData | null>(null)
  const [loading, setLoading] = useState(true)
  const [dataSource, setDataSource] = useState<DataSource>(dataService.getDataSource())
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const unsub = dataService.onSourceChange((source) => setDataSource(source))
    return unsub
  }, [])

  // Listen for data invalidation (triggered after writes by ApplicationKit)
  useEffect(() => {
    const unsub = dataService.onDataInvalidate(() => {
      setRefreshKey(k => k + 1)
    })
    return unsub
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadData() {
      setLoading(true)
      try {
        const [dashResult, appResult, actionsResult, streakResult] = await Promise.all([
          dataService.getDashboard(),
          dataService.getApplications(),
          dataService.getNextActions(),
          dataService.getStreakData(),
        ])
        if (cancelled) return
        if (dashResult.data) {
          setKpis(dashResult.data.kpis ?? [])
          setMonthlyData(dashResult.data.monthlyChart ?? [])
          setSourceData(dashResult.data.sourceChart ?? [])
        }
        setApplications(appResult.data ?? [])
        setNextActions(actionsResult.data ?? [])
        setStreakData(streakResult.data ?? null)
      } catch (e) {
        console.error('[Dashboard] loadData failed:', e)
        if (!cancelled) {
          setKpis([])
          setMonthlyData([])
          setSourceData([])
          setApplications([])
          setNextActions([])
          setStreakData(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    loadData()
    return () => { cancelled = true }
  }, [dataSource, refreshKey])

  const activeApps = applications.filter(
    (a) => !['Rejected', 'Ghosted', 'Saved'].includes(a.status),
  )
  const topApplications = [...activeApps]
    .sort((a, b) => b.fitScore - a.fitScore)
    .slice(0, 4)

  const offerCount = applications.filter((a) => a.status === 'Offer').length
  const urgentCount = applications.filter((a) => a.priority === 'Critical' || a.priority === 'High').length

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero greeting */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{mockProfile.greeting}, {mockProfile.name.split(' ')[0]} 👋</h1>
          <p className="text-sm text-text-secondary mt-1">
            You have <span className="text-accent-amber font-semibold">{urgentCount} urgent action{urgentCount !== 1 ? 's' : ''}</span> and{' '}
            <span className="text-accent-emerald font-semibold">{offerCount} offer{offerCount !== 1 ? 's' : ''}</span> waiting.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage('application-kit')}
            className="btn-primary text-sm"
          >+ New Application</button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {loading ? (
          <div className="col-span-full text-center py-4 text-sm text-text-muted">Loading KPIs...</div>
        ) : kpis.length > 0 ? (
          kpis.map((kpi) => (
            <KPICard key={kpi.label} kpi={kpi} />
          ))
        ) : (
          <div className="col-span-full text-center py-4 text-sm text-text-muted">No data available</div>
        )}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: Chart + Pipeline */}
        <div className="xl:col-span-2 space-y-6">
          {/* Monthly chart */}
          <Card>
            <CardHeader
              title="Application Activity"
              subtitle="Monthly applications, interviews & offers"
              icon={<TrendingUp size={18} />}
            />
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={monthlyData}>
                <defs>
                  <linearGradient id="colorApps" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorInt" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22D3EE" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22D3EE" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorOff" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#34D399" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2735" />
                <XAxis dataKey="month" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    background: '#11161F',
                    border: '1px solid #2A3650',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Area type="monotone" dataKey="applications" stroke="#6366F1" fill="url(#colorApps)" strokeWidth={2} />
                <Area type="monotone" dataKey="interviews" stroke="#22D3EE" fill="url(#colorInt)" strokeWidth={2} />
                <Area type="monotone" dataKey="offers" stroke="#34D399" fill="url(#colorOff)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
            {monthlyData.length === 0 && !loading && (
              <div className="text-center py-4 text-sm text-text-muted">No application activity yet</div>
            )}
          </Card>

          {/* Source distribution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader title="Application Sources" subtitle="Where applications come from" icon={<Briefcase size={18} />} />
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={sourceData}
                    dataKey="count"
                    nameKey="source"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {sourceData.map((_, i) => (
                      <Cell key={i} fill={SOURCE_COLORS[i % SOURCE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: '#11161F',
                      border: '1px solid #2A3650',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-3 mt-2">
                {sourceData.map((s, i) => (
                  <div key={s.source} className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: SOURCE_COLORS[i % SOURCE_COLORS.length] }} />
                    <span className="text-xs text-text-secondary">{s.source}</span>
                  </div>
                ))}
              </div>
              {sourceData.length === 0 && !loading && (
                <div className="text-center py-4 text-sm text-text-muted">No source data yet</div>
              )}
            </Card>

            {/* Streak + Goals */}
            <Card>
              <CardHeader title="Goals & Streak" subtitle="Daily and weekly progress" icon={<Flame size={18} />} />
              <div className="flex items-center gap-4 mb-4">
                <div className="flex flex-col items-center">
                  <div className="w-14 h-14 rounded-2xl bg-accent-amber/10 flex items-center justify-center">
                    <Flame size={26} className="text-accent-amber" />
                  </div>
                  <span className="text-2xl font-bold text-text-primary mt-2">{streakData?.currentStreak ?? 0}</span>
                  <span className="text-2xs text-text-muted">day streak</span>
                </div>
                <div className="flex-1 space-y-3">
                  <ProgressBar
                    value={streakData?.todayCount ?? 0}
                    max={streakData?.dailyGoal ?? 1}
                    label="Today"
                  />
                  <ProgressBar
                    value={streakData?.weekCount ?? 0}
                    max={streakData?.weeklyGoal ?? 1}
                    label="This Week"
                  />
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-border-subtle">
                <div className="flex items-center gap-1.5">
                  <Target size={14} className="text-text-muted" />
                  <span className="text-xs text-text-muted">Longest streak</span>
                </div>
                <span className="text-sm font-bold text-text-primary">{streakData?.longestStreak ?? 0} days</span>
              </div>
            </Card>
          </div>

          {/* Top applications */}
          <Card>
            <CardHeader
              title="Top Active Applications"
              subtitle="Highest fit score applications in progress"
              icon={<Zap size={18} />}
              action={
                <button
                  onClick={() => setPage('application-kit')}
                  className="btn-ghost text-xs flex items-center gap-1"
                >
                  View all <ArrowRight size={14} />
                </button>
              }
            />
            <div className="space-y-2">
              {loading ? (
                <div className="text-center py-6 text-sm text-text-muted">Loading...</div>
              ) : topApplications.length > 0 ? (
                topApplications.map((app) => (
                  <div
                    key={app.id}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-bg-surface2 transition-colors cursor-pointer"
                  >
                    <ScoreCircle score={app.fitScore} size="sm" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-text-primary truncate">{app.company}</span>
                        <StatusPill status={app.status} size="xs" />
                      </div>
                      <p className="text-xs text-text-secondary truncate">{app.role}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs text-text-muted">{app.salary}</p>
                      <p className="text-2xs text-text-muted mt-0.5">{app.workType}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-sm text-text-muted border border-dashed border-border-subtle rounded-xl">
                  No active applications yet
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right: Next Actions + Quick Stats */}
        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Next Best Actions"
              subtitle="AI-prioritized recommendations"
              icon={<Zap size={18} />}
            />
            <div className="space-y-2.5">
              {loading ? (
                <div className="text-center py-4 text-sm text-text-muted">Loading...</div>
              ) : nextActions.length > 0 ? (
                nextActions.map((action) => (
                  <NextActionCard key={action.id} action={action} />
                ))
              ) : (
                <div className="text-center py-4 text-sm text-text-muted border border-dashed border-border-subtle rounded-xl">
                  No actions yet
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="This Week" subtitle="Upcoming follow-ups" icon={<Calendar size={18} />} />
            <div className="space-y-2">
              {loading ? (
                <div className="text-center py-4 text-sm text-text-muted">Loading...</div>
              ) : applications.filter((a) => a.followUpDate).length > 0 ? (
                applications
                  .filter((a) => a.followUpDate)
                  .slice(0, 4)
                  .map((app) => (
                    <div key={app.id} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-bg-surface2 transition-colors">
                      <div className="w-1 h-10 rounded-full bg-accent-indigo" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">{app.company}</p>
                        <p className="text-xs text-text-muted truncate">{app.nextAction}</p>
                      </div>
                      <span className="text-2xs text-text-muted shrink-0">{app.followUpDate}</span>
                    </div>
                  ))
              ) : (
                <div className="text-center py-4 text-sm text-text-muted border border-dashed border-border-subtle rounded-xl">
                  No upcoming follow-ups
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
