import type {
  Application,
  ApplicationStatus,
  KPICard,
  NextAction,
  JDAnalysisResult,
  InterviewQuestion,
  StreakData,
  CoverLetterResult,
  LinkedInMessageResult,
  InterviewPracticeHistory,
} from './types'

export type DataSource = 'mock' | 'excel-readonly' | 'fallback'

export interface DataServiceResult<T> {
  data: T | null
  error: string | null
  source: DataSource
}

export interface WriteResult {
  success: boolean
  data?: { applicationId?: string; oldStatus?: string; newStatus?: string }
  backupPath?: string
  error?: string
}

export interface WriteModeResult {
  enabled: boolean
  mode?: string  // "demo", "staging", "production", or "disabled"
  reason: string
  workbookPath?: string
  workbookName?: string
  sessionBackupPath?: string | null
}

export interface WorkbookStatusResult {
  workbookName: string | null
  mode: string  // "mock", "read-only", "demo", "staging", "production"
  available: boolean
  schemaValid: boolean
  writeEnabled: boolean
  writeMode: string
  lastBackupFilename: string | null
  error: string | null
}

export interface SelectWorkbookResult {
  success: boolean
  selected: boolean
  cancelled: boolean
  workbookName: string | null
  mode: string | null
  schemaValid: boolean | null
  writeEnabled: boolean
  message: string | null
  error: string | null
}

export interface DataService {
  getApplications(): Promise<DataServiceResult<Application[]>>
  getKPIs(): Promise<DataServiceResult<KPICard[]>>
  getDashboard(): Promise<DataServiceResult<{
    kpis: KPICard[]
    monthlyChart: { month: string; applications: number; interviews: number; offers: number }[]
    sourceChart: { source: string; count: number }[]
    pipeline: { status: string; count: number }[]
  }>>
  getPipeline(): Promise<DataServiceResult<{ status: string; count: number }[]>>
  getInterviewQuestions(category?: string): Promise<DataServiceResult<InterviewQuestion[]>>
  getStreakData(): Promise<DataServiceResult<StreakData>>
  getNextActions(): Promise<DataServiceResult<NextAction[]>>
  analyzeJobDescription(payload: { jobDescription: string; candidateSkills?: string[] }): Promise<DataServiceResult<JDAnalysisResult>>
  generateCoverLetter(payload: { company: string; role: string; name: string; years?: string; field?: string; tone?: string; achievement?: string; jobDescription?: string; notes?: string }): Promise<DataServiceResult<CoverLetterResult>>
  generateLinkedInMessage(payload: { messageType: string; recipientName: string; recipientRole?: string; company: string; yourName: string; yourRole?: string; field?: string; years?: string; targetRole?: string; highlight?: string; notes?: string }): Promise<DataServiceResult<LinkedInMessageResult>>
  saveInterviewPractice(payload: { questionId: string; question: string; category: string; answer: string; elapsedSeconds: number; selfRating: number; notes?: string }): Promise<WriteResult>
  getInterviewPracticeHistory(): Promise<DataServiceResult<InterviewPracticeHistory>>
  exportReport(type?: string): Promise<DataServiceResult<{ content: string; filename: string }>>
  getDataSource(): DataSource
  onSourceChange(cb: (source: DataSource) => void): () => void
  // Core MVP write methods
  addApplication(data: Partial<Application>): Promise<WriteResult>
  updateApplicationStatus(id: string, status: ApplicationStatus): Promise<WriteResult>
  editApplication(id: string, data: Partial<Application>): Promise<WriteResult>
  // Write mode check
  getWriteMode(): Promise<WriteModeResult>
  // Workbook status
  getWorkbookStatus(): Promise<WorkbookStatusResult>
  // Workbook selection — opens native file dialog, validates, reinitializes backend
  selectWorkbook(): Promise<SelectWorkbookResult>
  // Data invalidation — triggers refresh across all subscribed components
  invalidate(): void
  onDataInvalidate(cb: () => void): () => void
}

// ── AutoAdapter ────────────────────────────────────────────────────────────────
// Checks pywebview availability lazily on each call (not at import time).
// Falls back to MockAdapter if pywebview is not ready or API call fails.
// Tracks the actual source from the last result for UI indicator accuracy.

import { MockAdapter } from './adapters/MockAdapter'
import { DesktopAdapter } from './adapters/DesktopAdapter'

class AutoAdapter implements DataService {
  private mock = new MockAdapter()
  private desktop = new DesktopAdapter()
  private currentSource: DataSource = 'mock'
  private listeners: ((source: DataSource) => void)[] = []
  private invalidateListeners: (() => void)[] = []
  private pywebviewReady = false

  constructor() {
    // Listen for pywebview ready event — fires when js_api is available
    if (typeof window !== 'undefined') {
      window.addEventListener('pywebviewready', () => {
        if (import.meta.env.DEV) console.log('[AutoAdapter] pywebviewready event fired')
        this.pywebviewReady = true
        // Notify listeners so components can re-fetch with real data
        this.currentSource = 'excel-readonly'
        this.notifyListeners()
      })
    }
  }

  private isDesktopAvailable(): boolean {
    // Check both: pywebviewready event fired OR window.pywebview.api exists directly
    // This handles cases where the event fires before React mounts
    return typeof window !== 'undefined' && !!window.pywebview?.api
  }

  private async dispatch<T>(
    method: keyof DataService,
    ...args: any[]
  ): Promise<DataServiceResult<T>> {
    let result: DataServiceResult<T>
    try {
      if (this.isDesktopAvailable()) {
        const fn = (this.desktop as any)[method] as (...a: any[]) => Promise<DataServiceResult<T>>
        if (import.meta.env.DEV) console.log(`[AutoAdapter] dispatching ${method} via DesktopAdapter`)
        result = await fn.call(this.desktop, ...args)
      } else {
        const fn = (this.mock as any)[method] as (...a: any[]) => Promise<DataServiceResult<T>>
        if (import.meta.env.DEV) console.log(`[AutoAdapter] dispatching ${method} via MockAdapter`)
        result = await fn.call(this.mock, ...args)
      }
    } catch (e) {
      // Desktop adapter threw — return error, do NOT fall back to mock
      console.warn(`[AutoAdapter] ${method} threw:`, e)
      result = { data: null, error: String(e), source: this.currentSource }
    }

    // Null safety on result — preserve valid error responses
    if (!result) {
      result = { data: null, error: 'No data returned', source: 'fallback' }
    }

    if (result.source !== this.currentSource) {
      this.currentSource = result.source
      this.notifyListeners()
    }
    return result
  }

  private notifyListeners() {
    for (const cb of this.listeners) {
      cb(this.currentSource)
    }
  }

  onSourceChange(cb: (source: DataSource) => void): () => void {
    this.listeners.push(cb)
    return () => {
      this.listeners = this.listeners.filter(l => l !== cb)
    }
  }

  async getApplications(): Promise<DataServiceResult<Application[]>> {
    return this.dispatch<Application[]>('getApplications')
  }

  async getKPIs(): Promise<DataServiceResult<KPICard[]>> {
    return this.dispatch<KPICard[]>('getKPIs')
  }

  async getDashboard(): Promise<DataServiceResult<{
    kpis: KPICard[]
    monthlyChart: { month: string; applications: number; interviews: number; offers: number }[]
    sourceChart: { source: string; count: number }[]
    pipeline: { status: string; count: number }[]
  }>> {
    return this.dispatch('getDashboard')
  }

  async getPipeline(): Promise<DataServiceResult<{ status: string; count: number }[]>> {
    return this.dispatch('getPipeline')
  }

  async getInterviewQuestions(category?: string): Promise<DataServiceResult<InterviewQuestion[]>> {
    return this.dispatch<InterviewQuestion[]>('getInterviewQuestions', category)
  }

  async getStreakData(): Promise<DataServiceResult<StreakData>> {
    return this.dispatch<StreakData>('getStreakData')
  }

  async getNextActions(): Promise<DataServiceResult<NextAction[]>> {
    return this.dispatch<NextAction[]>('getNextActions')
  }

  async analyzeJobDescription(payload: { jobDescription: string; candidateSkills?: string[] }): Promise<DataServiceResult<JDAnalysisResult>> {
    return this.dispatch<JDAnalysisResult>('analyzeJobDescription', payload)
  }

  async generateCoverLetter(payload: { company: string; role: string; name: string; years?: string; field?: string; tone?: string; achievement?: string; jobDescription?: string; notes?: string }): Promise<DataServiceResult<CoverLetterResult>> {
    return this.dispatch<CoverLetterResult>('generateCoverLetter', payload)
  }

  async generateLinkedInMessage(payload: { messageType: string; recipientName: string; recipientRole?: string; company: string; yourName: string; yourRole?: string; field?: string; years?: string; targetRole?: string; highlight?: string; notes?: string }): Promise<DataServiceResult<LinkedInMessageResult>> {
    return this.dispatch<LinkedInMessageResult>('generateLinkedInMessage', payload)
  }

  async saveInterviewPractice(payload: { questionId: string; question: string; category: string; answer: string; elapsedSeconds: number; selfRating: number; notes?: string }): Promise<WriteResult> {
    if (this.isDesktopAvailable()) {
      try {
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('save_interview_practice timed out')), 10000)
        })
        const api = (window as any).pywebview.api
        const result = await Promise.race([
          api.save_interview_practice(payload),
          timeoutPromise,
        ])
        if (result?.success === true) {
          // Practice history changed — invalidate so history panel refreshes
          this.invalidate()
        }
        return result ?? { success: false, error: 'No response from API' }
      } catch (e) {
        return { success: false, error: String(e) }
      }
    }
    return { success: false, error: 'Saving practice answers requires the desktop application.' }
  }

  async getInterviewPracticeHistory(): Promise<DataServiceResult<InterviewPracticeHistory>> {
    return this.dispatch<InterviewPracticeHistory>('getInterviewPracticeHistory')
  }

  async exportReport(type?: string): Promise<DataServiceResult<{ content: string; filename: string }>> {
    return this.dispatch<{ content: string; filename: string }>('exportReport', { type: type || 'monthly' })
  }

  getDataSource(): DataSource {
    return this.currentSource
  }

  // Core MVP write methods — dispatch to desktop, emit invalidation on success only
  private async writeAndInvalidate<T extends { success?: boolean }>(
    operation: () => Promise<T>
  ): Promise<T> {
    if (this.isDesktopAvailable()) {
      try {
        const result = await operation()
        if (result?.success === true) {
          this.invalidate()
        }
        return result
      } catch (e) {
        return { success: false, error: String(e) } as unknown as T
      }
    }
    return { success: false, error: 'Write actions are only enabled for demo/test workbooks in this phase.' } as unknown as T
  }

  async addApplication(data: Partial<Application>): Promise<WriteResult> {
    return this.writeAndInvalidate(async () => {
      const api = (window as any).pywebview.api
      return await api.add_application(data)
    })
  }

  async updateApplicationStatus(id: string, status: ApplicationStatus): Promise<WriteResult> {
    return this.writeAndInvalidate(async () => {
      const api = (window as any).pywebview.api
      return await api.update_application_status(id, status)
    })
  }

  async getWriteMode(): Promise<WriteModeResult> {
    if (this.isDesktopAvailable()) {
      try {
        const api = (window as any).pywebview.api
        const result = await api.get_write_mode()
        return result ?? { enabled: false, reason: 'No response from API' }
      } catch (e) {
        return { enabled: false, reason: String(e) }
      }
    }
    return { enabled: false, reason: 'Mock mode — write actions require demo workbook' }
  }

  async editApplication(id: string, data: Partial<Application>): Promise<WriteResult> {
    return this.writeAndInvalidate(async () => {
      const api = (window as any).pywebview.api
      return await api.edit_application(id, data)
    })
  }

  async getWorkbookStatus(): Promise<WorkbookStatusResult> {
    if (this.isDesktopAvailable()) {
      try {
        const api = (window as any).pywebview.api
        const result = await api.get_workbook_status()
        return result ?? {
          workbookName: null, mode: 'mock', available: false,
          schemaValid: false, writeEnabled: false, writeMode: 'disabled',
          lastBackupFilename: null, error: 'No response from API',
        }
      } catch (e) {
        return {
          workbookName: null, mode: 'mock', available: false,
          schemaValid: false, writeEnabled: false, writeMode: 'disabled',
          lastBackupFilename: null, error: String(e),
        }
      }
    }
    return {
      workbookName: null, mode: 'mock', available: false,
      schemaValid: false, writeEnabled: false, writeMode: 'disabled',
      lastBackupFilename: null, error: null,
    }
  }

  async selectWorkbook(): Promise<SelectWorkbookResult> {
    if (this.isDesktopAvailable()) {
      try {
        const api = (window as any).pywebview.api
        const result = await api.select_workbook()
        if (result?.success === true && result?.selected === true) {
          this.currentSource = 'excel-readonly'
          this.notifyListeners()
          this.invalidate()
        }
        return result ?? {
          success: false, selected: false, cancelled: false,
          workbookName: null, mode: null, schemaValid: false,
          writeEnabled: false, message: null, error: 'No response from API',
        }
      } catch (e) {
        return {
          success: false, selected: false, cancelled: false,
          workbookName: null, mode: null, schemaValid: false,
          writeEnabled: false, message: null, error: String(e),
        }
      }
    }
    return {
      success: false, selected: false, cancelled: false,
      workbookName: null, mode: null, schemaValid: false,
      writeEnabled: false, message: null,
      error: 'Workbook selection requires the desktop application.',
    }
  }

  invalidate(): void {
    for (const cb of this.invalidateListeners) {
      try { cb() } catch (e) { console.warn('[AutoAdapter] invalidate listener error:', e) }
    }
  }

  onDataInvalidate(cb: () => void): () => void {
    this.invalidateListeners.push(cb)
    return () => {
      this.invalidateListeners = this.invalidateListeners.filter(l => l !== cb)
    }
  }
}

export const dataService: DataService = new AutoAdapter()
