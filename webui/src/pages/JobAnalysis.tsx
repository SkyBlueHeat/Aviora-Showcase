import { useState, useRef } from 'react'
import { Card, CardHeader } from '@/components/Card'
import { ScoreCircle } from '@/components/ScoreCircle'
import { dataService } from '@/lib/dataService'
import type { JDAnalysisResult } from '@/lib/types'
import {
  FileSearch,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Lightbulb,
  DollarSign,
  Briefcase,
  Code2,
  Sparkles,
  Loader2,
  AlertCircle,
} from 'lucide-react'

export function JobAnalysis() {
  const [jdText, setJdText] = useState('')
  const [skills, setSkills] = useState('')
  const [analyzed, setAnalyzed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<JDAnalysisResult | null>(null)
  const reqIdRef = useRef(0)

  const handleAnalyze = async () => {
    if (jdText.trim().length < 20) return
    const reqId = ++reqIdRef.current
    setLoading(true)
    setError(null)
    setAnalyzed(true)
    try {
      const candidateSkills = skills
        .split(/[,\n]/)
        .map(s => s.trim())
        .filter(Boolean)
      const res = await dataService.analyzeJobDescription({
        jobDescription: jdText,
        candidateSkills,
      })
      if (reqId !== reqIdRef.current) return
      if (res.error) {
        setError(res.error)
        setResult(null)
      } else if (res.data) {
        setResult(res.data)
      } else {
        setError('Analysis returned no data.')
        setResult(null)
      }
    } catch (e) {
      if (reqId !== reqIdRef.current) return
      setError('An unexpected error occurred during analysis.')
      setResult(null)
    } finally {
      if (reqId === reqIdRef.current) setLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Job Description Analysis</h1>
        <p className="text-sm text-text-secondary mt-1">
          Paste a job description to get AI-powered insights, fit score, and keyword recommendations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Paste Job Description"
              subtitle="The more text you provide, the better the analysis"
              icon={<FileSearch size={18} />}
            />
            <textarea
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value)
                setAnalyzed(false)
                setResult(null)
                setError(null)
              }}
              placeholder="Paste the full job description here..."
              className="w-full h-64 bg-bg-surface2 border border-border-subtle rounded-lg p-4 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:border-accent-indigo focus:ring-1 focus:ring-accent-indigo/30 transition-all"
            />
            <div className="mt-3">
              <label className="text-xs font-medium text-text-secondary mb-1.5 block">
                Your Skills (optional, comma-separated)
              </label>
              <input
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="React, TypeScript, Python, AWS..."
                className="input-field w-full"
              />
            </div>
            <div className="flex items-center justify-between mt-3">
              <span className="text-xs text-text-muted">{jdText.length} characters</span>
              <button
                onClick={handleAnalyze}
                disabled={jdText.trim().length < 20 || loading}
                className="btn-primary text-sm flex items-center gap-2"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </Card>

          {analyzed && !loading && result && (
            <Card className="animate-slide-up">
              <CardHeader title="Summary" icon={<Lightbulb size={18} />} />
              <p className="text-sm text-text-secondary leading-relaxed">{result.summary}</p>
            </Card>
          )}
        </div>

        {/* Right: Results */}
        {analyzed ? (
          loading ? (
            <Card className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <Loader2 size={32} className="animate-spin text-accent-indigo mx-auto mb-4" />
                <p className="text-sm text-text-muted">Analyzing job description...</p>
              </div>
            </Card>
          ) : error ? (
            <Card className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-accent-rose/10 flex items-center justify-center text-accent-rose mx-auto mb-4">
                  <AlertCircle size={32} />
                </div>
                <h3 className="text-sm font-semibold text-text-primary mb-1">Analysis Failed</h3>
                <p className="text-xs text-text-muted max-w-xs">{error}</p>
              </div>
            </Card>
          ) : result ? (
            <div className="space-y-4 animate-slide-up">
              <Card>
                <div className="flex items-center gap-6">
                  <ScoreCircle score={result.fitScore} size="lg" label="Fit Score" />
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-2.5">
                      <Briefcase size={16} className="text-accent-cyan" />
                      <div>
                        <p className="text-2xs text-text-muted">Seniority</p>
                        <p className="text-sm font-semibold text-text-primary">{result.seniority}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <DollarSign size={16} className="text-accent-emerald" />
                      <div>
                        <p className="text-2xs text-text-muted">Salary Estimate</p>
                        <p className="text-sm font-semibold text-text-primary">{result.salaryEstimate}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <CardHeader title="Tech Stack" icon={<Code2 size={18} />} />
                <div className="flex flex-wrap gap-2">
                  {result.techStack.length > 0 ? (
                    result.techStack.map((tech) => (
                      <span key={tech} className="badge bg-accent-indigo/15 text-accent-indigo">
                        {tech}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-text-muted">No tech keywords detected.</span>
                  )}
                </div>
              </Card>

              <Card>
                <CardHeader title="Green Flags" icon={<CheckCircle2 size={18} />} />
                <div className="space-y-2">
                  {result.greenFlags.length > 0 ? (
                    result.greenFlags.map((flag) => (
                      <div key={flag} className="flex items-start gap-2">
                        <CheckCircle2 size={16} className="text-accent-emerald shrink-0 mt-0.5" />
                        <span className="text-sm text-text-secondary">{flag}</span>
                      </div>
                    ))
                  ) : (
                    <span className="text-xs text-text-muted">No green flags detected.</span>
                  )}
                </div>
              </Card>

              <Card>
                <CardHeader title="Red Flags" icon={<AlertTriangle size={18} />} />
                <div className="space-y-2">
                  {result.redFlags.length > 0 ? (
                    result.redFlags.map((flag) => (
                      <div key={flag} className="flex items-start gap-2">
                        <XCircle size={16} className="text-accent-rose shrink-0 mt-0.5" />
                        <span className="text-sm text-text-secondary">{flag}</span>
                      </div>
                    ))
                  ) : (
                    <span className="text-xs text-text-muted">No red flags detected.</span>
                  )}
                </div>
              </Card>

              <Card>
                <CardHeader
                  title="Missing Keywords"
                  subtitle="Add these to your resume for better ATS score"
                  icon={<AlertTriangle size={18} />}
                />
                <div className="flex flex-wrap gap-2 mb-3">
                  {result.missingKeywords.length > 0 ? (
                    result.missingKeywords.map((kw) => (
                      <span key={kw} className="badge bg-accent-rose/10 text-accent-rose">
                        {kw}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-text-muted">No missing keywords — great match!</span>
                  )}
                </div>
                {result.matchedKeywords.length > 0 && (
                  <div className="pt-3 border-t border-border-subtle">
                    <p className="text-xs font-semibold text-text-primary mb-2">Matched Keywords</p>
                    <div className="flex flex-wrap gap-2">
                      {result.matchedKeywords.map((kw) => (
                        <span key={kw} className="badge bg-accent-emerald/10 text-accent-emerald">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            </div>
          ) : null
        ) : (
          <Card className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-bg-surface2 flex items-center justify-center text-text-muted mx-auto mb-4">
                <FileSearch size={32} />
              </div>
              <h3 className="text-sm font-semibold text-text-primary mb-1">No analysis yet</h3>
              <p className="text-xs text-text-muted max-w-xs">
                Paste a job description on the left and click Analyze to see detailed insights.
              </p>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
