import { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardHeader } from '@/components/Card'
import { dataService } from '@/lib/dataService'
import type { InterviewQuestion, InterviewPracticeHistory } from '@/lib/types'
import { mockStarChecklist } from '@/lib/mockData'
import {
  MessageSquare,
  Star,
  CheckCircle2,
  Timer,
  History,
  Zap,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const categories = ['All', 'Behavioral', 'Technical'] as const
const difficultyConfig = {
  Easy: { bg: 'bg-accent-emerald/10', text: 'text-accent-emerald' },
  Medium: { bg: 'bg-accent-amber/10', text: 'text-accent-amber' },
  Hard: { bg: 'bg-accent-rose/10', text: 'text-accent-rose' },
}

export function InterviewPrep() {
  const [category, setCategory] = useState<string>('All')
  const [questions, setQuestions] = useState<InterviewQuestion[]>([])
  const [loadingQuestions, setLoadingQuestions] = useState(true)
  const [selected, setSelected] = useState<InterviewQuestion | null>(null)
  const [answer, setAnswer] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(false)
  const [selfRating, setSelfRating] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [history, setHistory] = useState<InterviewPracticeHistory | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const loadQuestions = useCallback(async (cat: string) => {
    setLoadingQuestions(true)
    try {
      const res = await dataService.getInterviewQuestions(cat === 'All' ? undefined : cat)
      if (!mountedRef.current) return
      if (res.data) {
        setQuestions(res.data)
      } else if (res.error) {
        setQuestions([])
      }
    } catch {
      if (mountedRef.current) setQuestions([])
    } finally {
      if (mountedRef.current) setLoadingQuestions(false)
    }
  }, [])

  const loadHistory = useCallback(async () => {
    try {
      const res = await dataService.getInterviewPracticeHistory()
      if (!mountedRef.current) return
      if (res.data) {
        setHistory(res.data)
      }
    } catch {
      // silent fail
    }
  }, [])

  useEffect(() => {
    loadQuestions(category)
  }, [category, loadQuestions])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    if (running) {
      timerRef.current = setInterval(() => {
        setElapsed((prev) => prev + 1)
      }, 1000)
    } else if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [running])

  const handleSelect = (q: InterviewQuestion) => {
    setSelected(q)
    setAnswer('')
    setElapsed(0)
    setRunning(true)
    setSelfRating(0)
    setSubmitError(null)
    setSubmitSuccess(false)
  }

  const handleSubmit = async () => {
    if (!selected || !answer.trim() || selfRating < 1) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const res = await dataService.saveInterviewPractice({
        questionId: selected.id,
        question: selected.question,
        category: selected.category,
        answer: answer.trim(),
        elapsedSeconds: elapsed,
        selfRating,
      })
      if (res.success) {
        if (!mountedRef.current) return
        setSubmitSuccess(true)
        setRunning(false)
        loadHistory()
      } else {
        if (mountedRef.current) setSubmitError(res.error || 'Failed to save practice answer.')
      }
    } catch {
      if (mountedRef.current) setSubmitError('An unexpected error occurred while saving.')
    } finally {
      if (mountedRef.current) setSubmitting(false)
    }
  }

  const handleReset = () => {
    setRunning(false)
    setElapsed(0)
    setAnswer('')
    setSelfRating(0)
    setSubmitError(null)
    setSubmitSuccess(false)
  }

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  const wordCount = answer.split(/\s+/).filter(Boolean).length

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Interview Prep</h1>
        <p className="text-sm text-text-secondary mt-1">
          Practice with real interview questions. Use STAR framework for behavioral answers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Question list + STAR checklist */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                  category === cat
                    ? 'bg-accent-indigo text-white'
                    : 'bg-bg-surface2 text-text-secondary hover:bg-bg-hover',
                )}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="space-y-2">
            {loadingQuestions ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="animate-spin text-accent-indigo" />
              </div>
            ) : questions.length === 0 ? (
              <p className="text-xs text-text-muted text-center py-4">No questions found.</p>
            ) : (
              questions.map((q) => (
                <button
                  key={q.id}
                  onClick={() => handleSelect(q)}
                  className={cn(
                    'w-full text-left card p-3 card-hover',
                    selected?.id === q.id && 'border-accent-indigo ring-1 ring-accent-indigo/20',
                  )}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-accent-indigo">{q.category}</span>
                    <span className={cn('badge text-2xs', difficultyConfig[q.difficulty].bg, difficultyConfig[q.difficulty].text)}>
                      {q.difficulty}
                    </span>
                  </div>
                  <p className="text-sm text-text-primary line-clamp-2">{q.question}</p>
                </button>
              ))
            )}
          </div>

          {/* STAR Checklist */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Star size={16} className="text-accent-violet" />
              <span className="text-sm font-semibold text-text-primary">STAR Checklist</span>
            </div>
            <div className="space-y-2.5">
              {mockStarChecklist.map((item) => (
                <div key={item.letter} className="flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-accent-violet/15 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-accent-violet">{item.letter}</span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-text-primary">{item.label}</p>
                    <p className="text-2xs text-text-muted">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Middle: Practice area */}
        <div className="lg:col-span-6">
          {selected ? (
            <Card>
              <CardHeader
                title={selected.category}
                subtitle={selected.difficulty}
                icon={<MessageSquare size={18} />}
                action={
                  <div className="flex items-center gap-2 text-sm">
                    <Timer size={16} className="text-accent-cyan" />
                    <span className="font-mono font-semibold text-text-primary">{formatTime(elapsed)}</span>
                  </div>
                }
              />
              <div className="space-y-4">
                <div className="bg-bg-surface2 rounded-lg p-4">
                  <p className="text-sm font-semibold text-text-primary mb-1">Question:</p>
                  <p className="text-sm text-text-secondary leading-relaxed">{selected.question}</p>
                  {selected.tips && selected.tips.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border-subtle">
                      <p className="text-xs font-semibold text-text-muted mb-1">Tips:</p>
                      <ul className="space-y-1">
                        {selected.tips.map((tip) => (
                          <li key={tip} className="text-xs text-text-secondary flex items-start gap-1.5">
                            <CheckCircle2 size={12} className="text-accent-emerald shrink-0 mt-0.5" />
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div>
                  <label className="text-xs font-medium text-text-secondary mb-1.5 block">Your Answer</label>
                  <textarea
                    value={answer}
                    onChange={(e) => {
                      setAnswer(e.target.value)
                      setSubmitSuccess(false)
                    }}
                    placeholder="Type your answer here..."
                    className="w-full h-40 bg-bg-surface2 border border-border-subtle rounded-lg p-4 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:border-accent-indigo focus:ring-1 focus:ring-accent-indigo/30"
                  />
                </div>

                {/* Self-rating */}
                <div>
                  <label className="text-xs font-medium text-text-secondary mb-1.5 block">Rate your answer (1-5)</label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        onClick={() => setSelfRating(n)}
                        className={cn(
                          'w-10 h-10 rounded-lg text-sm font-bold transition-all',
                          selfRating === n
                            ? 'bg-accent-indigo text-white'
                            : 'bg-bg-surface2 text-text-secondary hover:bg-bg-hover',
                        )}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>

                {submitError && (
                  <div className="flex items-center gap-2 text-xs text-accent-rose bg-accent-rose/10 rounded-lg p-3">
                    <AlertCircle size={14} />
                    {submitError}
                  </div>
                )}

                {submitSuccess && (
                  <div className="flex items-center gap-2 text-xs text-accent-emerald bg-accent-emerald/10 rounded-lg p-3 animate-slide-up">
                    <CheckCircle2 size={14} />
                    Practice answer saved! View it in your history.
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-xs text-text-muted">{wordCount} words</span>
                  <div className="flex items-center gap-2">
                    <button onClick={handleReset} className="btn-ghost text-sm">
                      Reset
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={!answer.trim() || selfRating < 1 || submitting}
                      className="btn-primary text-sm flex items-center gap-2"
                    >
                      {submitting ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                      {submitting ? 'Saving...' : 'Submit Answer'}
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ) : (
            <Card className="flex items-center justify-center min-h-[300px]">
              <div className="text-center">
                <div className="w-14 h-14 rounded-2xl bg-bg-surface2 flex items-center justify-center text-text-muted mx-auto mb-3">
                  <MessageSquare size={28} />
                </div>
                <h3 className="text-sm font-semibold text-text-primary mb-1">Select a question</h3>
                <p className="text-xs text-text-muted max-w-xs">
                  Choose a question from the left to start practicing. Timer starts automatically.
                </p>
              </div>
            </Card>
          )}
        </div>

        {/* Right: Practice History + Stats */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <History size={16} className="text-accent-cyan" />
              <span className="text-sm font-semibold text-text-primary">Practice History</span>
            </div>
            {history && history.entries.length > 0 ? (
              <div className="space-y-2.5 max-h-[300px] overflow-y-auto">
                {history.entries.slice().reverse().slice(0, 10).map((entry) => (
                  <div
                    key={entry.id}
                    className="p-3 rounded-lg bg-bg-surface2 border border-border-subtle hover:border-border transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-2xs font-semibold text-accent-indigo">{entry.category}</span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-2xs font-bold text-text-primary">{entry.selfRating}</span>
                        <span className="text-2xs text-text-muted">/5</span>
                      </div>
                    </div>
                    <p className="text-xs text-text-secondary line-clamp-2 mb-1">{entry.question}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-2xs text-text-muted">{entry.wordCount} words</span>
                      <span className="text-2xs text-text-muted">·</span>
                      <span className="text-2xs text-text-muted">{formatTime(Math.round(entry.elapsedSeconds))}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-text-muted text-center py-4">
                No practice history yet. Submit an answer to get started.
              </p>
            )}
          </Card>

          {/* Quick stats */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={16} className="text-accent-amber" />
              <span className="text-sm font-semibold text-text-primary">Practice Stats</span>
            </div>
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">Answers practiced</span>
                <span className="text-sm font-bold text-text-primary">{history?.stats.totalAnswers ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">Avg. self-rating</span>
                <span className="text-sm font-bold text-accent-emerald">
                  {history?.stats.avgScore ? `${history.stats.avgScore}/5` : '—'}
                </span>
              </div>
              {history && history.stats.byCategory && Object.entries(history.stats.byCategory).map(([cat, avg]) => (
                <div key={cat} className="flex items-center justify-between">
                  <span className="text-xs text-text-secondary">{cat} avg</span>
                  <span className="text-sm font-bold text-accent-cyan">{avg}/5</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
