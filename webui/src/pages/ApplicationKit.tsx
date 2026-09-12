import { useState, useEffect, useCallback, useRef } from 'react'
import { Card } from '@/components/Card'
import { StatusPill } from '@/components/StatusPill'
import { ScoreCircle } from '@/components/ScoreCircle'
import { pipelineColumns } from '@/lib/mockData'
import { dataService } from '@/lib/dataService'
import type { DataSource, WriteModeResult, WorkbookStatusResult } from '@/lib/dataService'
import type { ApplicationStatus, Application } from '@/lib/types'
import {
  Plus,
  MapPin,
  DollarSign,
  Search,
  Filter,
  LayoutGrid,
  List,
  X,
  CheckCircle,
  AlertCircle,
  FlaskConical,
  ShieldCheck,
  FileWarning,
  Pencil,
  Database,
  FolderOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const ALL_STATUSES: ApplicationStatus[] = [
  'Saved', 'Applied', 'Phone Screen', 'Technical', 'Onsite', 'Offer', 'Rejected', 'Ghosted',
]

// ── Main Component ────────────────────────────────────────────────────────────

export function ApplicationKit() {
  const [view, setView] = useState<'kanban' | 'list'>('kanban')
  const [search, setSearch] = useState('')
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [dataSource, setDataSource] = useState<DataSource>(dataService.getDataSource())
  const [writeMode, setWriteMode] = useState<WriteModeResult>({ enabled: false, reason: 'Checking...' })
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingApp, setEditingApp] = useState<Application | null>(null)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [updatingId, setUpdatingId] = useState<string | null>(null)
  const [prodConfirmed, setProdConfirmed] = useState(false)
  const [showProdConfirm, setShowProdConfirm] = useState(false)
  const [workbookStatus, setWorkbookStatus] = useState<WorkbookStatusResult | null>(null)
  const [selectingWorkbook, setSelectingWorkbook] = useState(false)
  const pendingActionRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    const unsub = dataService.onSourceChange((source) => setDataSource(source))
    return unsub
  }, [])

  const loadApplications = useCallback(async () => {
    setLoading(true)
    try {
      const result = await dataService.getApplications()
      setApplications(result.data ?? [])
    } catch (e) {
      console.error('[ApplicationKit] loadData failed:', e)
      setApplications([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadApplications()
    dataService.getWriteMode().then(setWriteMode)
    dataService.getWorkbookStatus().then(setWorkbookStatus)
  }, [dataSource, loadApplications])

  // Listen for data invalidation (triggered after writes by other components)
  useEffect(() => {
    const unsub = dataService.onDataInvalidate(() => {
      loadApplications()
      dataService.getWriteMode().then(setWriteMode)
      dataService.getWorkbookStatus().then(setWorkbookStatus)
    })
    return unsub
  }, [loadApplications])

  const showFeedback = useCallback((type: 'success' | 'error', msg: string) => {
    setFeedback({ type, msg })
    setTimeout(() => setFeedback(null), 4000)
  }, [])

  const handleProdConfirm = useCallback(() => {
    setProdConfirmed(true)
    setShowProdConfirm(false)
    const action = pendingActionRef.current
    pendingActionRef.current = null
    if (action) action()
  }, [])

  const handleProdCancel = useCallback(() => {
    setShowProdConfirm(false)
    pendingActionRef.current = null
  }, [])

  const handleAddApplication = async (data: Record<string, string>): Promise<{ success: boolean; error?: string }> => {
    return new Promise((resolve) => {
      const doAdd = async () => {
        const result = await dataService.addApplication({
          company: data.company,
          role: data.role,
          status: (data.status as ApplicationStatus) || 'Saved',
          location: data.location,
          source: data.source,
          salary: data.salary,
          fitScore: parseInt(data.fitScore) || 0,
          notes: data.notes,
        })
        if (result.success) {
          setShowAddModal(false)
          showFeedback('success', `Added: ${data.role} at ${data.company}`)
          // Invalidation is emitted by AutoAdapter on success — no duplicate call here
        } else {
          showFeedback('error', result.error ?? 'Failed to add application.')
        }
        resolve({ success: result.success, error: result.error })
      }
      if (writeMode.mode === 'production' && !prodConfirmed) {
        pendingActionRef.current = doAdd
        setShowProdConfirm(true)
      } else {
        doAdd()
      }
    })
  }

  const handleStatusChange = useCallback(async (app: Application, newStatus: ApplicationStatus) => {
    if (newStatus === app.status || updatingId === app.id) return
    setUpdatingId(app.id)
    const doUpdate = async () => {
      try {
        const result = await dataService.updateApplicationStatus(app.id, newStatus)
        if (result.success) {
          showFeedback('success', `${app.company}: ${app.status} → ${newStatus}`)
          // Invalidation is emitted by AutoAdapter on success — no duplicate call here
        } else {
          showFeedback('error', result.error ?? 'Failed to update status.')
        }
      } catch (e) {
        showFeedback('error', String(e))
      } finally {
        setUpdatingId(null)
      }
    }
    if (writeMode.mode === 'production' && !prodConfirmed) {
      pendingActionRef.current = doUpdate
      setShowProdConfirm(true)
    } else {
      doUpdate()
    }
  }, [updatingId, loadApplications, showFeedback, writeMode.mode, prodConfirmed])

  const handleEditApplication = useCallback(async (app: Application, data: Record<string, string>): Promise<{ success: boolean; error?: string }> => {
    return new Promise((resolve) => {
      const doEdit = async () => {
        const result = await dataService.editApplication(app.id, {
          company: data.company,
          role: data.role,
          location: data.location,
          source: data.source,
          salary: data.salary,
          fitScore: parseInt(data.fitScore) || 0,
          notes: data.notes,
        })
        if (result.success) {
          setEditingApp(null)
          showFeedback('success', `Updated: ${data.role} at ${data.company}`)
          // Invalidation is emitted by AutoAdapter on success — no duplicate call here
        } else {
          showFeedback('error', result.error ?? 'Failed to edit application.')
        }
        resolve({ success: result.success, error: result.error })
      }
      if (writeMode.mode === 'production' && !prodConfirmed) {
        pendingActionRef.current = doEdit
        setShowProdConfirm(true)
      } else {
        doEdit()
      }
    })
  }, [loadApplications, showFeedback, writeMode.mode, prodConfirmed])

  const handleSelectWorkbook = useCallback(async () => {
    setSelectingWorkbook(true)
    try {
      const result = await dataService.selectWorkbook()
      if (result.cancelled) {
        // Do not show any toast for cancellation
      } else if (result.success && result.selected) {
        // Reset production confirmation state — new workbook is read-only
        setProdConfirmed(false)
        setShowProdConfirm(false)
        pendingActionRef.current = null
        // Close any open modals
        setShowAddModal(false)
        setEditingApp(null)
        // Show success with read-only notice
        showFeedback('success', result.message || `Workbook loaded: ${result.workbookName} (read-only)`)
        // Invalidation is emitted by AutoAdapter — listeners will refresh
      } else if (result.error) {
        showFeedback('error', result.error)
      }
    } catch (e) {
      showFeedback('error', String(e))
    } finally {
      setSelectingWorkbook(false)
    }
  }, [showFeedback])

  const filtered = applications.filter(
    (a) =>
      a.company.toLowerCase().includes(search.toLowerCase()) ||
      a.role.toLowerCase().includes(search.toLowerCase()),
  )

  const appsByStatus = (status: ApplicationStatus) =>
    filtered.filter((a) => a.status === status)

  const newAppTitle = writeMode.enabled
    ? `Add a new application to the ${writeMode.mode === 'production' ? 'production' : writeMode.mode === 'staging' ? 'staging' : 'demo'} workbook`
    : (writeMode.reason || 'Write actions are only enabled for demo/test/staging/production workbooks.')

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Feedback toast */}
      {feedback && (
        <div className={cn(
          'fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl text-sm font-medium pointer-events-none',
          feedback.type === 'success'
            ? 'bg-emerald-900/95 text-emerald-200 border border-emerald-700'
            : 'bg-rose-900/95 text-rose-200 border border-rose-700',
        )}>
          {feedback.type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
          {feedback.msg}
        </div>
      )}

      {/* Workbook Status Bar */}
      {workbookStatus && (
        <div className="flex items-center gap-4 flex-wrap text-xs px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle">
          <span className="flex items-center gap-1.5 text-text-secondary">
            <Database size={12} className="text-text-muted" />
            {workbookStatus.workbookName ?? 'No workbook'}
          </span>
          <span className={cn(
            'px-2 py-0.5 rounded-full border font-medium',
            workbookStatus.mode === 'production' ? 'text-rose-400 bg-rose-950/40 border-rose-800/50' :
            workbookStatus.mode === 'staging' ? 'text-amber-400 bg-amber-950/40 border-amber-800/50' :
            workbookStatus.mode === 'demo' ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50' :
            workbookStatus.mode === 'read-only' ? 'text-blue-400 bg-blue-950/40 border-blue-800/50' :
            'text-text-muted bg-bg-surface2 border-border-subtle'
          )}>
            {workbookStatus.mode === 'production' ? 'Production' :
             workbookStatus.mode === 'staging' ? 'Staging' :
             workbookStatus.mode === 'demo' ? 'Demo' :
             workbookStatus.mode === 'read-only' ? 'Read-only' : 'Mock'}
          </span>
          <span className={cn(
            'flex items-center gap-1',
            workbookStatus.available ? 'text-emerald-400' : 'text-rose-400'
          )}>
            {workbookStatus.available ? '● Available' : '● Missing'}
          </span>
          <span className={cn(
            'flex items-center gap-1',
            workbookStatus.schemaValid ? 'text-emerald-400' : 'text-rose-400'
          )}>
            {workbookStatus.schemaValid ? '● Schema OK' : '● Schema invalid'}
          </span>
          <span className={cn(
            'flex items-center gap-1',
            workbookStatus.writeEnabled ? 'text-emerald-400' : 'text-text-muted'
          )}>
            {workbookStatus.writeEnabled ? '● Writes enabled' : '● Writes disabled'}
          </span>
          {workbookStatus.lastBackupFilename && (
            <span className="text-text-muted truncate max-w-[200px]" title={workbookStatus.lastBackupFilename}>
              Last backup: {workbookStatus.lastBackupFilename}
            </span>
          )}
          {dataSource !== 'mock' && (
            <button
              onClick={handleSelectWorkbook}
              disabled={selectingWorkbook}
              className="ml-auto flex items-center gap-1 px-2 py-0.5 rounded border border-border-subtle hover:border-indigo-600 hover:text-indigo-400 transition-colors disabled:opacity-50"
              title="Select a different workbook file"
            >
              <FolderOpen size={12} />
              {selectingWorkbook ? 'Opening...' : 'Select Workbook'}
            </button>
          )}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Application Pipeline</h1>
          <p className="text-sm text-text-secondary mt-1">
            {loading
              ? 'Loading...'
              : `${filtered.length} applications · ${filtered.filter((a) => a.status === 'Offer').length} offers · ${filtered.filter((a) => !['Rejected', 'Ghosted', 'Saved'].includes(a.status)).length} active`}
          </p>
          {writeMode.enabled && (
            <span className={cn(
              'inline-flex items-center gap-1.5 mt-1 text-xs font-medium',
              writeMode.mode === 'production' ? 'text-rose-400' : writeMode.mode === 'staging' ? 'text-amber-400' : 'text-emerald-400',
            )}>
              {writeMode.mode === 'production' ? <FileWarning size={11} /> : writeMode.mode === 'staging' ? <ShieldCheck size={11} /> : <FlaskConical size={11} />}
              {writeMode.mode === 'production' ? 'Production' : writeMode.mode === 'staging' ? 'Staging' : 'Demo'} write mode — {writeMode.workbookName}
            </span>
          )}
        </div>
        <button
          disabled={!writeMode.enabled}
          title={newAppTitle}
          onClick={() => { if (writeMode.enabled) setShowAddModal(true) }}
          className={cn(
            'btn-primary text-sm flex items-center gap-2',
            !writeMode.enabled && 'opacity-50 cursor-not-allowed',
          )}
        >
          <Plus size={16} />
          New Application
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search applications..."
            className="input-field pl-9 w-full"
          />
        </div>
        <button className="btn-secondary text-sm flex items-center gap-2">
          <Filter size={14} />
          Filter
        </button>
        <div className="flex items-center gap-1 bg-bg-surface border border-border-subtle rounded-lg p-1">
          <button
            onClick={() => setView('kanban')}
            className={cn(
              'p-1.5 rounded-md transition-colors',
              view === 'kanban' ? 'bg-bg-surface2 text-text-primary' : 'text-text-muted hover:text-text-primary',
            )}
          >
            <LayoutGrid size={16} />
          </button>
          <button
            onClick={() => setView('list')}
            className={cn(
              'p-1.5 rounded-md transition-colors',
              view === 'list' ? 'bg-bg-surface2 text-text-primary' : 'text-text-muted hover:text-text-primary',
            )}
          >
            <List size={16} />
          </button>
        </div>
      </div>

      {/* Empty Workbook / First-Run Experience */}
      {!loading && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-bg-surface2 flex items-center justify-center text-text-muted mb-4">
            <Database size={28} />
          </div>
          <h3 className="text-sm font-semibold text-text-primary mb-1">
            {workbookStatus && !workbookStatus.available
              ? 'No workbook found'
              : 'No applications yet'}
          </h3>
          <p className="text-xs text-text-muted max-w-sm mb-4">
            {workbookStatus && !workbookStatus.available
              ? 'Launch with a valid workbook file, or set the JOBTRACKER_WORKBOOK_PATH environment variable to get started.'
              : workbookStatus && !workbookStatus.schemaValid
              ? 'The workbook is missing required headers (Application ID, Company, Role, Status). Please check the Applications sheet.'
              : 'Add applications using the New Application button, or add rows directly to the Applications sheet in your workbook.'}
          </p>
          {writeMode.enabled && (
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary text-sm flex items-center gap-2"
            >
              <Plus size={16} />
              Add Your First Application
            </button>
          )}
        </div>
      )}

      {/* Kanban View */}
      {view === 'kanban' && (
        loading ? (
          <div className="text-center py-12 text-sm text-text-muted">Loading applications...</div>
        ) : (
          <div className="overflow-x-auto pb-4 -mx-1 px-1 kanban-scroll">
            <div className="flex gap-3 min-w-max pb-2">
              {pipelineColumns.map((col) => {
                const apps = appsByStatus(col.status)
                return (
                  <div key={col.status} className="w-[260px] shrink-0">
                    <div className="flex items-center justify-between mb-2.5 px-1">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ background: col.color }} />
                        <span className="text-sm font-semibold text-text-primary">{col.label}</span>
                      </div>
                      <span className="text-xs font-bold text-text-muted bg-bg-surface2 px-2 py-0.5 rounded-full min-w-[24px] text-center">
                        {apps.length}
                      </span>
                    </div>
                    <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
                      {apps.map((app) => (
                        <KanbanCard
                          key={app.id}
                          app={app}
                          writeModeEnabled={writeMode.enabled}
                          updating={updatingId === app.id}
                          onStatusChange={handleStatusChange}
                          onEdit={() => setEditingApp(app)}
                        />
                      ))}
                      {apps.length === 0 && (
                        <div className="text-center py-6 text-xs text-text-muted border border-dashed border-border-subtle rounded-xl">
                          No applications in this stage
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      )}

      {/* List View */}
      {view === 'list' && (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px]">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Company</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Role</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Status</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Fit</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Salary</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Location</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-sm text-text-muted">Loading applications...</td>
                  </tr>
                ) : filtered.length > 0 ? (
                  filtered.map((app) => (
                    <tr
                      key={app.id}
                      className="border-b border-border-subtle last:border-0 hover:bg-bg-surface2 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <span className="text-sm font-semibold text-text-primary">{app.company}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-secondary">{app.role}</span>
                      </td>
                      <td className="px-4 py-3">
                        {writeMode.enabled ? (
                          <select
                            value={app.status}
                            disabled={updatingId === app.id}
                            onChange={(e) => handleStatusChange(app, e.target.value as ApplicationStatus)}
                            className={cn(
                              'text-xs rounded-md border border-border-subtle bg-bg-surface2 text-text-primary px-2 py-1 cursor-pointer',
                              updatingId === app.id && 'opacity-50 cursor-not-allowed',
                            )}
                          >
                            {ALL_STATUSES.map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        ) : (
                          <StatusPill status={app.status} size="xs" />
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <ScoreCircle score={app.fitScore} size="sm" />
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-secondary">{app.salary}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs text-text-muted">{app.location}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-text-muted">{app.appliedDate || '—'}</span>
                          {writeMode.enabled && (
                            <button
                              onClick={() => setEditingApp(app)}
                              title="Edit"
                              className="p-1 rounded text-text-muted hover:text-accent-indigo hover:bg-bg-surface2 transition-colors"
                            >
                              <Pencil size={12} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-sm text-text-muted border border-dashed border-border-subtle">
                      No applications found. Add rows to the Applications sheet, or use New Application in write mode.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Add Application Modal */}
      {showAddModal && (
        <AddApplicationModal
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddApplication}
          modeLabel={writeMode.mode === 'production' ? 'Production' : writeMode.mode === 'staging' ? 'Staging' : 'Demo'}
        />
      )}

      {/* Edit Application Modal */}
      {editingApp && (
        <EditApplicationModal
          app={editingApp}
          onClose={() => setEditingApp(null)}
          onSubmit={handleEditApplication}
          modeLabel={writeMode.mode === 'production' ? 'Production' : writeMode.mode === 'staging' ? 'Staging' : 'Demo'}
        />
      )}

      {/* Production Confirmation Dialog */}
      {showProdConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in">
          <div className="bg-surface-elevated border border-rose-700/50 rounded-2xl p-6 max-w-md mx-4 shadow-2xl">
            <div className="flex items-start gap-3 mb-4">
              <FileWarning size={24} className="text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-bold text-text-primary">Production Write Confirmation</h3>
                <p className="text-sm text-text-secondary mt-2">
                  You are about to modify your real Aviora workbook. A backup will be created automatically before every change.
                </p>
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={handleProdCancel}
                className="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-hover transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleProdConfirm}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-rose-600 text-white hover:bg-rose-500 transition-colors"
              >
                Confirm & Write
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── KanbanCard ────────────────────────────────────────────────────────────────

function KanbanCard({
  app,
  writeModeEnabled,
  updating,
  onStatusChange,
  onEdit,
}: {
  app: Application
  writeModeEnabled: boolean
  updating: boolean
  onStatusChange: (app: Application, status: ApplicationStatus) => void
  onEdit: () => void
}) {
  return (
    <div className="card p-3 card-hover group">
      <div className="flex items-start justify-between mb-2">
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-semibold text-text-primary truncate">{app.company}</h4>
          <p className="text-xs text-text-secondary truncate mt-0.5">{app.role}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {writeModeEnabled && (
            <button
              onClick={onEdit}
              title="Edit application"
              className="p-1 rounded text-text-muted hover:text-accent-indigo hover:bg-bg-surface2 transition-colors"
            >
              <Pencil size={12} />
            </button>
          )}
          <ScoreCircle score={app.fitScore} size="sm" />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-2">
        {writeModeEnabled ? (
          <select
            value={app.status}
            disabled={updating}
            onChange={(e) => onStatusChange(app, e.target.value as ApplicationStatus)}
            className={cn(
              'text-xs rounded-md border border-border-subtle bg-bg-surface2 text-text-primary px-2 py-0.5 cursor-pointer w-full',
              updating && 'opacity-50 cursor-not-allowed',
            )}
          >
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        ) : (
          <StatusPill status={app.status} size="xs" />
        )}
      </div>

      <div className="flex items-center gap-3 text-2xs text-text-muted">
        <span className="flex items-center gap-1 truncate">
          <DollarSign size={11} className="shrink-0" />
          <span className="truncate">{app.salary || '—'}</span>
        </span>
        <span className="flex items-center gap-1 shrink-0">
          <MapPin size={11} />
          {app.workType}
        </span>
      </div>

      {app.nextAction && (
        <div className="mt-2 pt-2 border-t border-border-subtle">
          <p className="text-2xs text-accent-amber font-medium truncate">→ {app.nextAction}</p>
        </div>
      )}
    </div>
  )
}

// ── AddApplicationModal ────────────────────────────────────────────────────────

function AddApplicationModal({
  onClose,
  onSubmit,
  modeLabel,
}: {
  onClose: () => void
  onSubmit: (data: Record<string, string>) => Promise<{ success: boolean; error?: string }>
  modeLabel: string
}) {
  const [form, setForm] = useState({
    company: '', role: '', status: 'Saved', location: '', source: '',
    salary: '', fitScore: '', notes: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const set = (key: string, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!form.company.trim() || !form.role.trim()) {
      setError('Company and Role are required.')
      return
    }
    setSubmitting(true)
    const result = await onSubmit(form)
    setSubmitting(false)
    if (!result.success) {
      setError(result.error ?? 'Write failed. Check that write mode is active.')
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-bg-surface border border-border-subtle rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
          <div>
            <h2 className="text-base font-bold text-text-primary">New Application</h2>
            <p className="text-xs text-text-muted mt-0.5">{modeLabel} write mode — adds to {modeLabel} workbook</p>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors p-1"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Required row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Company <span className="text-rose-400">*</span></label>
              <input
                value={form.company}
                onChange={(e) => set('company', e.target.value)}
                placeholder="e.g. Acme Corp"
                className="input-field w-full"
                autoFocus
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Role <span className="text-rose-400">*</span></label>
              <input
                value={form.role}
                onChange={(e) => set('role', e.target.value)}
                placeholder="e.g. Senior Engineer"
                className="input-field w-full"
              />
            </div>
          </div>

          {/* Status + Source */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Status</label>
              <select
                value={form.status}
                onChange={(e) => set('status', e.target.value)}
                className="input-field w-full"
              >
                {ALL_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Source</label>
              <input
                value={form.source}
                onChange={(e) => set('source', e.target.value)}
                placeholder="e.g. LinkedIn"
                className="input-field w-full"
              />
            </div>
          </div>

          {/* Location + Salary */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Location</label>
              <input
                value={form.location}
                onChange={(e) => set('location', e.target.value)}
                placeholder="e.g. San Francisco"
                className="input-field w-full"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Salary</label>
              <input
                value={form.salary}
                onChange={(e) => set('salary', e.target.value)}
                placeholder="e.g. $150k"
                className="input-field w-full"
              />
            </div>
          </div>

          {/* Fit Score */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-text-secondary">Fit Score (0–100)</label>
            <input
              type="number"
              min={0}
              max={100}
              value={form.fitScore}
              onChange={(e) => set('fitScore', e.target.value)}
              placeholder="e.g. 80"
              className="input-field w-full"
            />
          </div>

          {/* Notes */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-text-secondary">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => set('notes', e.target.value)}
              placeholder="Optional notes..."
              rows={3}
              className="input-field w-full resize-none"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-sm text-rose-400 bg-rose-900/20 border border-rose-800/40 rounded-lg px-3 py-2">
              <AlertCircle size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={cn('btn-primary flex-1', submitting && 'opacity-70 cursor-not-allowed')}
            >
              {submitting ? 'Adding...' : 'Add Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── EditApplicationModal ────────────────────────────────────────────────────────

function EditApplicationModal({
  app,
  onClose,
  onSubmit,
  modeLabel,
}: {
  app: Application
  onClose: () => void
  onSubmit: (app: Application, data: Record<string, string>) => Promise<{ success: boolean; error?: string }>
  modeLabel: string
}) {
  const [form, setForm] = useState({
    company: app.company || '',
    role: app.role || '',
    location: app.location || '',
    source: app.source || '',
    salary: app.salary || '',
    fitScore: String(app.fitScore || 0),
    notes: app.notes || '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const set = (key: string, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!form.company.trim() || !form.role.trim()) {
      setError('Company and Role are required.')
      return
    }
    setSubmitting(true)
    const result = await onSubmit(app, form)
    setSubmitting(false)
    if (!result.success) {
      setError(result.error ?? 'Edit failed. Please try again.')
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-bg-surface border border-border-subtle rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
          <div>
            <h2 className="text-base font-bold text-text-primary">Edit Application</h2>
            <p className="text-xs text-text-muted mt-0.5">{modeLabel} write mode — ID: {app.id}</p>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors p-1">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4 max-h-[70vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Company <span className="text-rose-400">*</span></label>
              <input value={form.company} onChange={(e) => set('company', e.target.value)} className="input-field w-full" autoFocus />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Role <span className="text-rose-400">*</span></label>
              <input value={form.role} onChange={(e) => set('role', e.target.value)} className="input-field w-full" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Location</label>
              <input value={form.location} onChange={(e) => set('location', e.target.value)} className="input-field w-full" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Source</label>
              <input value={form.source} onChange={(e) => set('source', e.target.value)} className="input-field w-full" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Salary</label>
              <input value={form.salary} onChange={(e) => set('salary', e.target.value)} className="input-field w-full" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary">Fit Score (0–100)</label>
              <input type="number" min={0} max={100} value={form.fitScore} onChange={(e) => set('fitScore', e.target.value)} className="input-field w-full" />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-text-secondary">Notes</label>
            <textarea value={form.notes} onChange={(e) => set('notes', e.target.value)} rows={3} className="input-field w-full resize-none" />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-rose-400 bg-rose-900/20 border border-rose-800/40 rounded-lg px-3 py-2">
              <AlertCircle size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={submitting} className={cn('btn-primary flex-1', submitting && 'opacity-70 cursor-not-allowed')}>
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
