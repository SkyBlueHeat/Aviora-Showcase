import type {
  Application,
  KPICard,
  NextAction,
  JDAnalysisResult,
  InterviewQuestion,
  StreakData,
  ApplicationStatus,
} from './types'

// ── Config Flags ──────────────────────────────────────────────────────────────
export const SHOW_MOCK_BADGE = true

// ── Mock Profile ──────────────────────────────────────────────────────────────
export const mockProfile = {
  name: 'Jordan Avery',
  initials: 'JA',
  role: 'Senior Software Engineer',
  status: 'Job Seeker · Active',
  greeting: 'Good morning',
}

// ── Mock Applications ─────────────────────────────────────────────────────────
export const mockApplications: Application[] = [
  {
    id: '1',
    company: 'Stripe',
    role: 'Senior Frontend Engineer',
    status: 'Technical',
    priority: 'Critical',
    workType: 'Remote',
    location: 'San Francisco, CA',
    appliedDate: '2026-06-20',
    salary: '$180k - $220k',
    fitScore: 92,
    qualityScore: 88,
    source: 'LinkedIn',
    techStack: ['React', 'TypeScript', 'GraphQL'],
    notes: 'Great team, had phone screen with Sarah. Technical round next week.',
    followUpDate: '2026-07-02',
    nextAction: 'Prepare for technical interview',
  },
  {
    id: '2',
    company: 'Vercel',
    role: 'Full Stack Engineer',
    status: 'Phone Screen',
    priority: 'High',
    workType: 'Remote',
    location: 'Remote',
    appliedDate: '2026-06-25',
    salary: '$160k - $200k',
    fitScore: 85,
    qualityScore: 72,
    source: 'Company Website',
    techStack: ['Next.js', 'Node.js', 'PostgreSQL'],
    notes: 'Recruiter reached out. Phone screen scheduled for Thursday.',
    followUpDate: '2026-07-03',
    nextAction: 'Phone screen with recruiter',
  },
  {
    id: '3',
    company: 'Figma',
    role: 'UI Platform Engineer',
    status: 'Applied',
    priority: 'High',
    workType: 'Hybrid',
    location: 'San Francisco, CA',
    appliedDate: '2026-06-28',
    salary: '$170k - $210k',
    fitScore: 78,
    qualityScore: 65,
    source: 'Referral',
    techStack: ['React', 'WebGL', 'Rust'],
    notes: 'Referred by Alex. Waiting for response.',
    followUpDate: '2026-07-05',
    nextAction: 'Follow up with Alex about referral status',
  },
  {
    id: '4',
    company: 'Linear',
    role: 'Product Engineer',
    status: 'Offer',
    priority: 'Critical',
    workType: 'Remote',
    location: 'Remote',
    appliedDate: '2026-06-10',
    salary: '$190k - $230k',
    fitScore: 95,
    qualityScore: 94,
    source: 'LinkedIn',
    techStack: ['React', 'TypeScript', 'GraphQL'],
    notes: 'Got offer! $210k base + equity. Need to negotiate.',
    followUpDate: '2026-07-01',
    nextAction: 'Negotiate salary — counter with $230k',
  },
  {
    id: '5',
    company: 'Supabase',
    role: 'Backend Engineer',
    status: 'Applied',
    priority: 'Medium',
    workType: 'Remote',
    location: 'Remote',
    appliedDate: '2026-06-30',
    salary: '$150k - $180k',
    fitScore: 72,
    qualityScore: 58,
    source: 'Job Board',
    techStack: ['PostgreSQL', 'Go', 'Kubernetes'],
    notes: 'Applied through job board. No response yet.',
    followUpDate: '2026-07-07',
    nextAction: 'Wait for response',
  },
  {
    id: '6',
    company: 'Datadog',
    role: 'Senior Software Engineer',
    status: 'Rejected',
    priority: 'Low',
    workType: 'Hybrid',
    location: 'New York, NY',
    appliedDate: '2026-06-05',
    salary: '$170k - $200k',
    fitScore: 68,
    qualityScore: 60,
    source: 'LinkedIn',
    techStack: ['Go', 'Python', 'Kafka'],
    notes: 'Rejected after technical round. Feedback: need more system design prep.',
    nextAction: 'Practice system design',
  },
  {
    id: '7',
    company: 'Notion',
    role: 'Frontend Engineer',
    status: 'Onsite',
    priority: 'Critical',
    workType: 'Hybrid',
    location: 'San Francisco, CA',
    appliedDate: '2026-06-15',
    salary: '$175k - $215k',
    fitScore: 88,
    qualityScore: 82,
    source: 'Referral',
    techStack: ['React', 'TypeScript', 'Electron'],
    notes: 'Onsite scheduled for next Monday. 4 rounds.',
    followUpDate: '2026-07-08',
    nextAction: 'Prepare onsite presentation',
  },
  {
    id: '8',
    company: 'Anthropic',
    role: 'ML Infrastructure Engineer',
    status: 'Ghosted',
    priority: 'Low',
    workType: 'On-site',
    location: 'San Francisco, CA',
    appliedDate: '2026-05-28',
    salary: '$200k - $250k',
    fitScore: 65,
    qualityScore: 45,
    source: 'Company Website',
    techStack: ['Python', 'PyTorch', 'CUDA'],
    notes: 'No response after 5 weeks. Likely ghosted.',
    nextAction: 'Move on',
  },
  {
    id: '9',
    company: 'Retool',
    role: 'Senior Product Engineer',
    status: 'Saved',
    priority: 'Medium',
    workType: 'Remote',
    location: 'Remote',
    salary: '$160k - $195k',
    fitScore: 80,
    qualityScore: 0,
    source: 'LinkedIn',
    techStack: ['React', 'TypeScript', 'Node.js'],
    notes: 'Interesting role, need to tailor resume before applying.',
    appliedDate: '',
    nextAction: 'Tailor resume and apply',
  },
  {
    id: '10',
    company: 'PlanetScale',
    role: 'Database Engineer',
    status: 'Applied',
    priority: 'Medium',
    workType: 'Remote',
    location: 'Remote',
    appliedDate: '2026-06-27',
    salary: '$155k - $185k',
    fitScore: 74,
    qualityScore: 62,
    source: 'Job Board',
    techStack: ['MySQL', 'Go', 'Kubernetes'],
    notes: 'Applied 3 days ago. No response yet.',
    followUpDate: '2026-07-04',
    nextAction: 'Wait for response',
  },
]

// ── Mock KPIs ─────────────────────────────────────────────────────────────────
export const mockKPIs: KPICard[] = [
  { label: 'Total Applications', value: 47, change: '+12 this week', trend: 'up', color: 'indigo' },
  { label: 'Active', value: 8, change: '3 in interview stage', trend: 'up', color: 'cyan' },
  { label: 'Interviews', value: 5, change: '+2 this week', trend: 'up', color: 'violet' },
  { label: 'Offers', value: 1, change: 'Linear — $210k', trend: 'up', color: 'emerald' },
  { label: 'Response Rate', value: '34%', change: '+5%', trend: 'up', color: 'amber' },
  { label: 'Ghosted', value: 3, change: '-1', trend: 'down', color: 'rose' },
]

// ── Mock Next Actions ─────────────────────────────────────────────────────────
export const mockNextActions: NextAction[] = [
  {
    id: '1',
    title: 'Negotiate Linear offer',
    description: 'Counter with $230k base. You have leverage with Stripe interview ongoing.',
    urgency: 'urgent',
    company: 'Linear',
    actionType: 'negotiate',
  },
  {
    id: '2',
    title: 'Follow up with Figma',
    description: 'Alex referred you 5 days ago. Send a gentle follow-up message.',
    urgency: 'today',
    company: 'Figma',
    actionType: 'follow-up',
  },
  {
    id: '3',
    title: 'Prepare for Stripe technical round',
    description: 'Focus on React performance, GraphQL caching, and system design.',
    urgency: 'this-week',
    company: 'Stripe',
    actionType: 'prep',
  },
  {
    id: '4',
    title: 'Apply to Retool',
    description: 'Tailor your resume to highlight React + TypeScript experience.',
    urgency: 'this-week',
    company: 'Retool',
    actionType: 'apply',
  },
  {
    id: '5',
    title: 'Connect with Notion hiring manager',
    description: 'Find the hiring manager on LinkedIn before your onsite.',
    urgency: 'this-week',
    company: 'Notion',
    actionType: 'network',
  },
]

// ── Mock JD Analysis ──────────────────────────────────────────────────────────
export const mockJDAnalysis: JDAnalysisResult = {
  seniority: 'Senior (5+ years)',
  salaryEstimate: '$170k - $210k',
  fitScore: 87,
  greenFlags: [
    'Clear tech stack mentioned (React, TypeScript, GraphQL)',
    'Remote-first culture',
    'Growth opportunities described',
    'Modern engineering practices (CI/CD, code review)',
  ],
  redFlags: [
    'Unlimited PTO (often means less actual vacation)',
    'Vague equity compensation',
    'On-call rotation not mentioned',
  ],
  missingKeywords: ['CI/CD', 'Jest', 'React Query', 'Storybook', 'Playwright'],
  matchedKeywords: ['React', 'TypeScript', 'GraphQL', 'Node.js', 'REST API', 'Agile'],
  recommendedKeywords: ['Add CI/CD pipeline experience to resume', 'Mention testing with Jest/Playwright', 'Highlight GraphQL caching strategies'],
  techStack: ['React', 'TypeScript', 'GraphQL', 'Node.js', 'AWS', 'PostgreSQL'],
  summary: 'Strong match for your profile. Senior frontend role at a well-funded startup. Focus on highlighting your React + GraphQL experience and testing practices.',
}

// ── Mock Interview Questions ──────────────────────────────────────────────────
export const mockInterviewQuestions: InterviewQuestion[] = [
  {
    id: 'q1',
    category: 'Behavioral',
    question: 'Tell me about a time you had a conflict with a teammate and how you resolved it.',
    difficulty: 'Medium',
    starFramework: {
      situation: 'At my previous company, a teammate and I disagreed on the architecture for a new feature.',
      task: 'I needed to find a compromise that satisfied both technical requirements and team harmony.',
      action: 'I scheduled a 1:1 to understand their concerns, then proposed a hybrid approach that addressed both our points.',
      result: 'We shipped the feature on time with a design both of us were happy with.',
    },
  },
  {
    id: 'q2',
    category: 'Technical',
    question: 'Explain how you would implement a virtual scrolling list in React.',
    difficulty: 'Hard',
  },
  {
    id: 'q3',
    category: 'System Design',
    question: 'Design a real-time notification system that handles 1M concurrent users.',
    difficulty: 'Hard',
  },
  {
    id: 'q4',
    category: 'Behavioral',
    question: 'Describe a project that failed. What did you learn?',
    difficulty: 'Medium',
  },
  {
    id: 'q5',
    category: 'Coding',
    question: 'Given an array of integers, find the longest subarray with sum equal to k.',
    difficulty: 'Medium',
  },
]

// ── Mock Saved Interview Answers ──────────────────────────────────────────────
export const mockSavedAnswers = [
  {
    id: 'a1',
    questionId: 'q1',
    question: 'Tell me about a time you had a conflict with a teammate.',
    answer: 'At my previous company, a teammate and I disagreed on the architecture for a new feature. I scheduled a 1:1 to understand their concerns, then proposed a hybrid approach. We shipped on time with a design both of us were happy with.',
    score: 82,
    savedAt: '2026-06-28',
    category: 'Behavioral',
  },
  {
    id: 'a2',
    questionId: 'q2',
    question: 'Explain how you would implement a virtual scrolling list in React.',
    answer: 'I would use a windowing technique — only render visible items plus a small overscan buffer. Track scroll position, calculate visible range from item height, and use absolute positioning or transform to place items.',
    score: 75,
    savedAt: '2026-06-29',
    category: 'Technical',
  },
]

// ── STAR Checklist ────────────────────────────────────────────────────────────
export const mockStarChecklist = [
  { letter: 'S', label: 'Situation', desc: 'Set the scene and provide context' },
  { letter: 'T', label: 'Task', desc: 'Describe your specific responsibility' },
  { letter: 'A', label: 'Action', desc: 'Explain exactly what steps you took' },
  { letter: 'R', label: 'Result', desc: 'Share the outcome and what you learned' },
]

// ── Mock Streak Data ──────────────────────────────────────────────────────────
export const mockStreakData: StreakData = {
  currentStreak: 12,
  longestStreak: 23,
  dailyGoal: 5,
  weeklyGoal: 20,
  todayCount: 3,
  weekCount: 14,
}

// ── Mock Chart Data ───────────────────────────────────────────────────────────
export const mockMonthlyData = [
  { month: 'Jan', applications: 8, interviews: 1, offers: 0 },
  { month: 'Feb', applications: 12, interviews: 2, offers: 0 },
  { month: 'Mar', applications: 6, interviews: 1, offers: 0 },
  { month: 'Apr', applications: 15, interviews: 3, offers: 1 },
  { month: 'May', applications: 10, interviews: 2, offers: 0 },
  { month: 'Jun', applications: 18, interviews: 5, offers: 1 },
]

export const mockSourceData = [
  { source: 'LinkedIn', count: 18 },
  { source: 'Referral', count: 8 },
  { source: 'Job Board', count: 12 },
  { source: 'Company Website', count: 9 },
]

// ── Pipeline Columns ──────────────────────────────────────────────────────────
export const pipelineColumns: { status: ApplicationStatus; label: string; color: string }[] = [
  { status: 'Saved', label: 'Saved', color: '#64748B' },
  { status: 'Applied', label: 'Applied', color: '#6366F1' },
  { status: 'Phone Screen', label: 'Phone Screen', color: '#22D3EE' },
  { status: 'Technical', label: 'Technical', color: '#A78BFA' },
  { status: 'Onsite', label: 'Onsite', color: '#FBBF24' },
  { status: 'Offer', label: 'Offer', color: '#34D399' },
  { status: 'Rejected', label: 'Rejected', color: '#F43F5E' },
  { status: 'Ghosted', label: 'Ghosted', color: '#64748B' },
]

// ── Mock Cover Letter ─────────────────────────────────────────────────────────
export const mockCoverLetter = `Dear Hiring Manager,

I am excited to apply for the Senior Frontend Engineer position at Stripe. With over 6 years of experience building performant React applications and a deep understanding of payment systems, I am confident I would be a strong addition to your team.

In my current role, I led the migration of a legacy monolith to a modern React + TypeScript architecture, reducing page load times by 40% and improving developer productivity by 25%. I also implemented a comprehensive testing strategy using Jest and Playwright, achieving 90% code coverage.

I am particularly drawn to Stripe's mission of increasing the GDP of the internet. Your commitment to developer experience and API design excellence aligns perfectly with my own engineering values.

I would welcome the opportunity to discuss how my experience in frontend performance optimization and design system development can contribute to Stripe's continued success.

Thank you for your consideration.

Best regards,
Jordan Avery`
