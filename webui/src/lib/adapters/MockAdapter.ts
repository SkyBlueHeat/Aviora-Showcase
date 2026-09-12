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
import {
  mockApplications,
  mockKPIs,
  mockNextActions,
  mockJDAnalysis,
  mockInterviewQuestions,
  mockStreakData,
  mockMonthlyData,
  mockSourceData,
  mockCoverLetter,
} from '../mockData'

export class MockAdapter implements DataService {
  private source: DataSource = 'mock'

  async getApplications(): Promise<DataServiceResult<Application[]>> {
    return { data: mockApplications, error: null, source: this.source }
  }

  async getKPIs(): Promise<DataServiceResult<KPICard[]>> {
    return { data: mockKPIs, error: null, source: this.source }
  }

  async getDashboard(): Promise<DataServiceResult<{
    kpis: KPICard[]
    monthlyChart: { month: string; applications: number; interviews: number; offers: number }[]
    sourceChart: { source: string; count: number }[]
    pipeline: { status: string; count: number }[]
  }>> {
    const pipeline = [
      'Saved', 'Applied', 'Phone Screen', 'Technical', 'Onsite', 'Offer', 'Rejected', 'Ghosted',
    ].map(status => ({
      status,
      count: mockApplications.filter(a => a.status === status).length,
    }))
    return {
      data: {
        kpis: mockKPIs,
        monthlyChart: mockMonthlyData,
        sourceChart: mockSourceData,
        pipeline,
      },
      error: null,
      source: this.source,
    }
  }

  async getPipeline(): Promise<DataServiceResult<{ status: string; count: number }[]>> {
    const pipeline = [
      'Saved', 'Applied', 'Phone Screen', 'Technical', 'Onsite', 'Offer', 'Rejected', 'Ghosted',
    ].map(status => ({
      status,
      count: mockApplications.filter(a => a.status === status).length,
    }))
    return { data: pipeline, error: null, source: this.source }
  }

  async getInterviewQuestions(category?: string): Promise<DataServiceResult<InterviewQuestion[]>> {
    if (category && category !== 'All') {
      return { data: mockInterviewQuestions.filter(q => q.category === category), error: null, source: this.source }
    }
    return { data: mockInterviewQuestions, error: null, source: this.source }
  }

  async getStreakData(): Promise<DataServiceResult<StreakData>> {
    return { data: mockStreakData, error: null, source: this.source }
  }

  async getNextActions(): Promise<DataServiceResult<NextAction[]>> {
    return { data: mockNextActions, error: null, source: this.source }
  }

  // ── Phase 2B mock methods (dev/test only) ─────────────────────────────────

  async analyzeJobDescription(_payload: { jobDescription: string; candidateSkills?: string[] }): Promise<DataServiceResult<JDAnalysisResult>> {
    return { data: mockJDAnalysis, error: null, source: this.source }
  }

  async generateCoverLetter(_payload: { company: string; role: string; name: string; years?: string; field?: string; tone?: string; achievement?: string; jobDescription?: string; notes?: string }): Promise<DataServiceResult<CoverLetterResult>> {
    return { data: { content: mockCoverLetter, mode: 'offline' as const, wordCount: mockCoverLetter.split(/\s+/).length }, error: null, source: this.source }
  }

  async generateLinkedInMessage(payload: { messageType: string; recipientName: string; recipientRole?: string; company: string; yourName: string; yourRole?: string; field?: string; years?: string; targetRole?: string; highlight?: string; notes?: string }): Promise<DataServiceResult<LinkedInMessageResult>> {
    const content = `Hi ${payload.recipientName.split(' ')[0]},\n\nI came across your profile while researching ${payload.company}. I'd love to connect and learn more about opportunities there.\n\nBest,\n${payload.yourName}`
    return { data: { content, messageType: payload.messageType, characterCount: content.length, characterLimit: 300 }, error: null, source: this.source }
  }

  async saveInterviewPractice(_payload: { questionId: string; question: string; category: string; answer: string; elapsedSeconds: number; selfRating: number; notes?: string }): Promise<WriteResult> {
    return { success: false, error: 'Mock mode — saving practice answers requires the desktop application.' }
  }

  async getInterviewPracticeHistory(): Promise<DataServiceResult<InterviewPracticeHistory>> {
    return { data: { entries: [], stats: { totalAnswers: 0, avgScore: 0, byCategory: {} } }, error: null, source: this.source }
  }

  async exportReport(_type?: string): Promise<DataServiceResult<{ content: string; filename: string }>> {
    return { data: { content: 'Mock mode — report generation requires the desktop application.', filename: 'mock_report.txt' }, error: null, source: this.source }
  }

  getDataSource(): DataSource {
    return this.source
  }

  onSourceChange(_cb: (source: DataSource) => void): () => void {
    return () => {}
  }

  // Phase 2B.2: Write mode check
  async getWriteMode(): Promise<WriteModeResult> {
    return { enabled: false, reason: 'Mock mode — write actions require demo workbook' }
  }

  // Write methods — mock always returns safe error (no desktop = no writes)
  async addApplication(_data: Partial<Application>): Promise<WriteResult> {
    return { success: false, error: 'Write actions are only enabled for demo/test/staging/production workbooks.' }
  }

  async updateApplicationStatus(_id: string, _status: ApplicationStatus): Promise<WriteResult> {
    return { success: false, error: 'Write actions are only enabled for demo/test/staging/production workbooks.' }
  }

  async editApplication(_id: string, _data: Partial<Application>): Promise<WriteResult> {
    return { success: false, error: 'Write actions are only enabled for demo/test/staging/production workbooks.' }
  }

  async getWorkbookStatus(): Promise<WorkbookStatusResult> {
    return {
      workbookName: null, mode: 'mock', available: false,
      schemaValid: false, writeEnabled: false, writeMode: 'disabled',
      lastBackupFilename: null, error: null,
    }
  }

  async selectWorkbook(): Promise<SelectWorkbookResult> {
    return {
      success: false,
      selected: false,
      cancelled: false,
      workbookName: null,
      mode: null,
      schemaValid: false,
      writeEnabled: false,
      message: null,
      error: 'Workbook selection requires the desktop application.',
    }
  }

  invalidate(): void {}

  onDataInvalidate(_cb: () => void): () => void {
    return () => {}
  }
}
