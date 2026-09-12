import type { DataService, DataServiceResult, DataSource, WriteResult, WriteModeResult, WorkbookStatusResult, SelectWorkbookResult } from '../dataService'
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
} from '../types'

declare global {
  interface Window {
    pywebview?: {
      api: {
        health(): Promise<any>
        get_applications(): Promise<any>
        get_dashboard(): Promise<any>
        get_kpis(): Promise<any>
        get_pipeline(): Promise<any>
        get_salary_data(): Promise<any>
        get_interview_history(): Promise<any>
        get_cover_letter_history(): Promise<any>
        add_application(data: any): Promise<WriteResult>
        update_application_status(id: string, status: string): Promise<WriteResult>
        edit_application(id: string, data: any): Promise<WriteResult>
        get_write_mode(): Promise<WriteModeResult>
        get_workbook_status(): Promise<WorkbookStatusResult>
        validate_workbook(path: string): Promise<any>
        select_workbook(): Promise<{ selected: boolean; workbookName?: string; reason?: string; validation?: any }>
        analyze_job_description(payload: any): Promise<any>
        generate_cover_letter(payload: any): Promise<any>
        generate_linkedin_message(payload: any): Promise<any>
        get_interview_questions(payload?: any): Promise<any>
        save_interview_practice(payload: any): Promise<any>
        get_interview_practice_history(): Promise<any>
        get_streak_data(): Promise<any>
        get_next_actions(): Promise<any>
        export_report(payload?: any): Promise<any>
      }
    }
  }
}

export class DesktopAdapter implements DataService {
  private source: DataSource = 'excel-readonly'
  private static TIMEOUT_MS = 10000

  private sanitizeError(e: unknown): string {
    const raw = String(e)
    // Remove file paths (Windows and Unix)
    let cleaned = raw.replace(/[A-Za-z]:\\[^\s'"<>]+/g, '[path]')
    cleaned = cleaned.replace(/\/[^\s'"<>]+/g, '[path]')
    // Remove env var names
    cleaned = cleaned.replace(/JOBTRACKER_\w+/g, '[env-var]')
    // Remove API key patterns
    cleaned = cleaned.replace(/sk-[A-Za-z0-9]{20,}/g, '[redacted]')
    // Remove traceback markers
    cleaned = cleaned.replace(/Traceback \(most recent call last\):/g, '')
    // Truncate if too long
    if (cleaned.length > 200) cleaned = cleaned.substring(0, 200) + '...'
    return cleaned.trim() || 'An unexpected error occurred'
  }

  private async call<T>(method: string, ...args: any[]): Promise<DataServiceResult<T>> {
    try {
      if (!window.pywebview?.api) {
        throw new Error('Desktop API not available')
      }
      const apiMethod = (window.pywebview.api as any)[method]
      if (typeof apiMethod !== 'function') {
        throw new Error(`Method ${method} not found on desktop API`)
      }

      if (import.meta.env.DEV) console.log(`[DesktopAdapter] calling ${method}...`)

      // Race the API call against a timeout so it can never hang forever
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error(`${method} timed out after ${DesktopAdapter.TIMEOUT_MS}ms`)), DesktopAdapter.TIMEOUT_MS)
      })

      const result = await Promise.race([
        apiMethod(...args),
        timeoutPromise,
      ])

      if (import.meta.env.DEV) console.log(`[DesktopAdapter] ${method} returned:`, result)

      // Null/undefined safety — return null data with error, no mock fallback
      if (result == null) {
        return { data: null, error: `${method} returned no data`, source: this.source }
      }

      // Check for error in the standard response format
      if (result.error && !result.success) {
        const errMsg = typeof result.error === 'object' ? (result.error.message || 'Unknown error') : result.error
        return { data: null, error: this.sanitizeError(errMsg), source: this.source }
      }

      // Success — pass through data (may be null if backend sent data: null)
      return { data: result.data ?? null, error: null, source: this.source }
    } catch (e) {
      const sanitized = this.sanitizeError(e)
      if (import.meta.env.DEV) console.warn(`[DesktopAdapter] ${method} failed:`, sanitized)
      return { data: null, error: sanitized, source: this.source }
    }
  }

  async getApplications(): Promise<DataServiceResult<Application[]>> {
    return this.call<Application[]>('get_applications')
  }

  async getKPIs(): Promise<DataServiceResult<KPICard[]>> {
    return this.call<KPICard[]>('get_kpis')
  }

  async getDashboard(): Promise<DataServiceResult<{
    kpis: KPICard[]
    monthlyChart: { month: string; applications: number; interviews: number; offers: number }[]
    sourceChart: { source: string; count: number }[]
    pipeline: { status: string; count: number }[]
  }>> {
    return this.call('get_dashboard')
  }

  async getPipeline(): Promise<DataServiceResult<{ status: string; count: number }[]>> {
    return this.call('get_pipeline')
  }

  async getInterviewQuestions(category?: string): Promise<DataServiceResult<InterviewQuestion[]>> {
    const payload = category ? { category } : {}
    return this.call<InterviewQuestion[]>('get_interview_questions', payload)
  }

  async getStreakData(): Promise<DataServiceResult<StreakData>> {
    return this.call<StreakData>('get_streak_data')
  }

  async getNextActions(): Promise<DataServiceResult<NextAction[]>> {
    return this.call<NextAction[]>('get_next_actions')
  }

  // ── Phase 2B new methods ──────────────────────────────────────────────────

  async analyzeJobDescription(payload: { jobDescription: string; candidateSkills?: string[] }): Promise<DataServiceResult<JDAnalysisResult>> {
    return this.call<JDAnalysisResult>('analyze_job_description', payload)
  }

  async generateCoverLetter(payload: { company: string; role: string; name: string; years?: string; field?: string; tone?: string; achievement?: string; jobDescription?: string; notes?: string }): Promise<DataServiceResult<CoverLetterResult>> {
    return this.call<CoverLetterResult>('generate_cover_letter', payload)
  }

  async generateLinkedInMessage(payload: { messageType: string; recipientName: string; recipientRole?: string; company: string; yourName: string; yourRole?: string; field?: string; years?: string; targetRole?: string; highlight?: string; notes?: string }): Promise<DataServiceResult<LinkedInMessageResult>> {
    return this.call<LinkedInMessageResult>('generate_linkedin_message', payload)
  }

  async saveInterviewPractice(payload: { questionId: string; question: string; category: string; answer: string; elapsedSeconds: number; selfRating: number; notes?: string }): Promise<WriteResult> {
    if (!window.pywebview?.api) {
      return { success: false, error: 'Desktop API not available' }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('save_interview_practice timed out')), DesktopAdapter.TIMEOUT_MS)
      })
      const result = await Promise.race([
        window.pywebview.api.save_interview_practice(payload),
        timeoutPromise,
      ])
      return result ?? { success: false, error: 'No response from API' }
    } catch (e) {
      return { success: false, error: this.sanitizeError(e) }
    }
  }

  async getInterviewPracticeHistory(): Promise<DataServiceResult<InterviewPracticeHistory>> {
    return this.call<InterviewPracticeHistory>('get_interview_practice_history')
  }

  async exportReport(type?: string): Promise<DataServiceResult<{ content: string; filename: string }>> {
    return this.call<{ content: string; filename: string }>('export_report', { type: type || 'monthly' })
  }

  getDataSource(): DataSource {
    return this.source
  }

  onSourceChange(_cb: (source: DataSource) => void): () => void {
    return () => {}
  }

  static isAvailable(): boolean {
    return typeof window !== 'undefined' && !!window.pywebview?.api
  }

  // Phase 2B.2: Write mode check
  async getWriteMode(): Promise<WriteModeResult> {
    if (!window.pywebview?.api) {
      return { enabled: false, reason: 'pywebview API not available' }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('get_write_mode timed out')), DesktopAdapter.TIMEOUT_MS)
      })
      const result = await Promise.race([
        window.pywebview.api.get_write_mode(),
        timeoutPromise,
      ])
      return result ?? { enabled: false, reason: 'No response from API' }
    } catch (e) {
      return { enabled: false, reason: String(e) }
    }
  }

  // Phase 2B.2: Demo-only write methods
  async addApplication(data: Partial<Application>): Promise<WriteResult> {
    if (!window.pywebview?.api) {
      return { success: false, error: 'pywebview API not available' }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('add_application timed out')), DesktopAdapter.TIMEOUT_MS)
      })
      return await Promise.race([
        window.pywebview.api.add_application(data),
        timeoutPromise,
      ])
    } catch (e) {
      return { success: false, error: this.sanitizeError(e) }
    }
  }

  async updateApplicationStatus(id: string, status: ApplicationStatus): Promise<WriteResult> {
    if (!window.pywebview?.api) {
      return { success: false, error: 'pywebview API not available' }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('update_application_status timed out')), DesktopAdapter.TIMEOUT_MS)
      })
      return await Promise.race([
        window.pywebview.api.update_application_status(id, status),
        timeoutPromise,
      ])
    } catch (e) {
      return { success: false, error: this.sanitizeError(e) }
    }
  }

  async editApplication(id: string, data: Partial<Application>): Promise<WriteResult> {
    if (!window.pywebview?.api) {
      return { success: false, error: 'pywebview API not available' }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('edit_application timed out')), DesktopAdapter.TIMEOUT_MS)
      })
      return await Promise.race([
        window.pywebview.api.edit_application(id, data),
        timeoutPromise,
      ])
    } catch (e) {
      return { success: false, error: this.sanitizeError(e) }
    }
  }

  async getWorkbookStatus(): Promise<WorkbookStatusResult> {
    if (!window.pywebview?.api) {
      return {
        workbookName: null, mode: 'mock', available: false,
        schemaValid: false, writeEnabled: false, writeMode: 'disabled',
        lastBackupFilename: null, error: 'pywebview API not available',
      }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('get_workbook_status timed out')), DesktopAdapter.TIMEOUT_MS)
      })
      return await Promise.race([
        window.pywebview.api.get_workbook_status(),
        timeoutPromise,
      ])
    } catch (e) {
      return {
        workbookName: null, mode: 'mock', available: false,
        schemaValid: false, writeEnabled: false, writeMode: 'disabled',
        lastBackupFilename: null, error: String(e),
      }
    }
  }

  async selectWorkbook(): Promise<SelectWorkbookResult> {
    if (!window.pywebview?.api) {
      return {
        success: false, selected: false, cancelled: false,
        workbookName: null, mode: null, schemaValid: false,
        writeEnabled: false, message: null,
        error: 'Workbook selection requires the desktop application.',
      }
    }
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('select_workbook timed out')), DesktopAdapter.TIMEOUT_MS * 2)
      })
      return await Promise.race([
        window.pywebview.api.select_workbook(),
        timeoutPromise,
      ]) as SelectWorkbookResult
    } catch (e) {
      return {
        success: false, selected: false, cancelled: false,
        workbookName: null, mode: null, schemaValid: false,
        writeEnabled: false, message: null,
        error: this.sanitizeError(e),
      }
    }
  }

  invalidate(): void {}

  onDataInvalidate(_cb: () => void): () => void {
    return () => {}
  }
}
