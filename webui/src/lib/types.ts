// ── Types for JobTracker PRO ──────────────────────────────────────────────────

export type ApplicationStatus =
  | 'Saved'
  | 'Applied'
  | 'Phone Screen'
  | 'Technical'
  | 'Onsite'
  | 'Offer'
  | 'Rejected'
  | 'Ghosted'

export type Priority = 'Critical' | 'High' | 'Medium' | 'Low'
export type WorkType = 'Remote' | 'Hybrid' | 'On-site'

export interface Application {
  id: string
  company: string
  role: string
  status: ApplicationStatus
  priority: Priority
  workType: WorkType
  location: string
  appliedDate: string
  salary: string
  fitScore: number
  qualityScore: number
  source: string
  techStack: string[]
  notes: string
  followUpDate?: string
  nextAction?: string
}

export interface KPICard {
  label: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  color: 'indigo' | 'cyan' | 'amber' | 'violet' | 'rose' | 'emerald'
}

export interface NextAction {
  id: string
  title: string
  description: string
  urgency: 'urgent' | 'today' | 'this-week' | 'someday'
  company?: string
  actionType: 'follow-up' | 'apply' | 'prep' | 'negotiate' | 'network'
  applicationId?: string
  role?: string
  dueDate?: string | null
}

export interface JDAnalysisResult {
  seniority: string
  salaryEstimate: string
  fitScore: number
  greenFlags: string[]
  redFlags: string[]
  missingKeywords: string[]
  matchedKeywords: string[]
  recommendedKeywords: string[]
  techStack: string[]
  summary: string
}

export interface CoverLetterResult {
  content: string
  mode: 'ai' | 'offline'
  wordCount: number
}

export interface LinkedInMessageResult {
  content: string
  messageType: string
  characterCount: number
  characterLimit: number
}

export interface InterviewQuestion {
  id: string
  category: 'Behavioral' | 'Technical' | 'System Design' | 'Coding'
  question: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  tips?: string[]
  starRelevant?: boolean
  starFramework?: {
    situation: string
    task: string
    action: string
    result: string
  }
}

export interface SalaryBreakdown {
  baseSalary: number
  bonusPct: number
  equity: number
  signingBonus: number
  benefits: number
  taxBracket: string
  totalComp: number
  netAnnual: number
  netMonthly: number
}

export interface StreakData {
  currentStreak: number
  longestStreak: number
  dailyGoal: number
  weeklyGoal: number
  todayCount: number
  weekCount: number
  lastActiveDate?: string | null
}

export interface InterviewPracticeEntry {
  id: string
  question: string
  category: string
  answer: string
  score: number
  selfRating: number
  elapsedSeconds: number
  wordCount: number
  completedAt: string
  notes: string
}

export interface InterviewPracticeHistory {
  entries: InterviewPracticeEntry[]
  stats: {
    totalAnswers: number
    avgScore: number
    byCategory: Record<string, number>
  }
}

export type PageId =
  | 'dashboard'
  | 'job-analysis'
  | 'application-kit'
  | 'cover-letter'
  | 'linkedin'
  | 'interview-prep'
  | 'salary-calc'
