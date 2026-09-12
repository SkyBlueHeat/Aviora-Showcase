import { useState, useRef } from 'react'
import { Card, CardHeader } from '@/components/Card'
import { dataService } from '@/lib/dataService'
import type { CoverLetterResult } from '@/lib/types'
import {
  PenLine,
  Copy,
  FileDown,
  Sparkles,
  RefreshCw,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const tones = [
  { id: 'professional', label: 'Professional' },
  { id: 'enthusiastic', label: 'Enthusiastic' },
  { id: 'concise', label: 'Concise' },
] as const

export function CoverLetterStudio() {
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [name, setName] = useState('')
  const [years, setYears] = useState('3')
  const [achievement, setAchievement] = useState('')
  const [jdText, setJdText] = useState('')
  const [tone, setTone] = useState<'professional' | 'enthusiastic' | 'concise'>('professional')
  const [result, setResult] = useState<CoverLetterResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const reqIdRef = useRef(0)

  const handleGenerate = async () => {
    if (!company.trim() || !role.trim() || !name.trim()) return
    const reqId = ++reqIdRef.current
    setLoading(true)
    setError(null)
    try {
      const res = await dataService.generateCoverLetter({
        company: company.trim(),
        role: role.trim(),
        name: name.trim(),
        years: years.trim(),
        tone,
        achievement: achievement.trim(),
        jobDescription: jdText.trim(),
      })
      if (reqId !== reqIdRef.current) return
      if (res.error) {
        setError(res.error)
        setResult(null)
      } else if (res.data) {
        setResult(res.data)
      }
    } catch (e) {
      if (reqId !== reqIdRef.current) return
      setError('An unexpected error occurred during generation.')
      setResult(null)
    } finally {
      if (reqId === reqIdRef.current) setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!result?.content) return
    try {
      await navigator.clipboard.writeText(result.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Failed to copy to clipboard. Please copy manually.')
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Cover Letter Studio</h1>
        <p className="text-sm text-text-secondary mt-1">
          Generate a tailored cover letter with live preview. Edit inputs and regenerate instantly.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Inputs (2/5) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader title="Details" subtitle="Fill in the details about the role" icon={<PenLine size={18} />} />

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Company Name *</label>
                <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Stripe" className="input-field w-full" />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Job Title *</label>
                <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Senior Frontend Engineer" className="input-field w-full" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-text-secondary mb-1.5 block">Your Name *</label>
                  <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Jordan Avery" className="input-field w-full" />
                </div>
                <div>
                  <label className="text-xs font-medium text-text-secondary mb-1.5 block">Years Experience</label>
                  <input value={years} onChange={(e) => setYears(e.target.value)} className="input-field w-full" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Key Achievement</label>
                <textarea
                  value={achievement}
                  onChange={(e) => setAchievement(e.target.value)}
                  rows={3}
                  placeholder="e.g. Led migration of legacy monolith to React + TypeScript, reducing load times by 40%"
                  className="input-field w-full resize-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Job Description (optional)</label>
                <textarea
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  rows={3}
                  placeholder="Paste the job description for better tailoring..."
                  className="input-field w-full resize-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Tone</label>
                <div className="flex gap-2">
                  {tones.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTone(t.id)}
                      className={cn(
                        'px-3 py-2 rounded-lg text-xs font-medium transition-all',
                        tone === t.id
                          ? 'bg-accent-indigo text-white'
                          : 'bg-bg-surface2 text-text-secondary hover:bg-bg-hover',
                      )}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>
              <button
                onClick={handleGenerate}
                disabled={!company.trim() || !role.trim() || !name.trim() || loading}
                className="btn-primary w-full text-sm flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                {loading ? 'Generating...' : 'Generate Cover Letter'}
              </button>
            </div>
          </Card>
        </div>

        {/* Right: Preview (3/5) */}
        <div className="lg:col-span-3">
          <Card className="h-full">
            <CardHeader
              title="Live Preview"
              subtitle="Generated cover letter — edit and regenerate as needed"
              icon={<FileDown size={18} />}
              action={
                <div className="flex items-center gap-2">
                  {result && (
                    <>
                      <span className={cn(
                        'badge text-2xs',
                        result.mode === 'ai' ? 'bg-accent-violet/15 text-accent-violet' : 'bg-bg-surface2 text-text-muted',
                      )}>
                        {result.mode === 'ai' ? 'AI' : 'Offline'}
                      </span>
                      <button onClick={handleGenerate} disabled={loading} className="btn-ghost text-xs flex items-center gap-1.5">
                        <RefreshCw size={14} />
                        Regenerate
                      </button>
                      <button onClick={handleCopy} className="btn-secondary text-xs flex items-center gap-1.5">
                        <Copy size={14} />
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </>
                  )}
                </div>
              }
            />
            {loading ? (
              <div className="flex items-center justify-center min-h-[500px]">
                <div className="text-center">
                  <Loader2 size={32} className="animate-spin text-accent-indigo mx-auto mb-4" />
                  <p className="text-sm text-text-muted">Generating cover letter...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center min-h-[500px]">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-accent-rose/10 flex items-center justify-center text-accent-rose mx-auto mb-4">
                    <AlertCircle size={32} />
                  </div>
                  <h3 className="text-sm font-semibold text-text-primary mb-1">Generation Failed</h3>
                  <p className="text-xs text-text-muted max-w-xs">{error}</p>
                </div>
              </div>
            ) : result ? (
              <div className="bg-white rounded-lg p-8 min-h-[500px]">
                <div className="font-serif text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                  {result.content}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-400">
                  {result.wordCount} words
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center min-h-[500px]">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-bg-surface2 flex items-center justify-center text-text-muted mx-auto mb-4">
                    <PenLine size={32} />
                  </div>
                  <h3 className="text-sm font-semibold text-text-primary mb-1">No cover letter yet</h3>
                  <p className="text-xs text-text-muted max-w-xs">
                    Fill in the details on the left and click Generate to create a tailored cover letter.
                  </p>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
