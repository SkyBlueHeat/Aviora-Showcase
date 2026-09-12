import { useState, useRef } from 'react'
import { Card, CardHeader } from '@/components/Card'
import { dataService } from '@/lib/dataService'
import type { LinkedInMessageResult } from '@/lib/types'
import {
  Linkedin,
  Copy,
  Sparkles,
  User,
  Building2,
  Briefcase,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const messageTypes = [
  { id: 'connection', label: 'Connection Request', desc: 'Connect with someone at a target company' },
  { id: 'referral', label: 'Referral Request', desc: 'Ask for a referral from a connection' },
  { id: 'recruiter', label: 'Recruiter Outreach', desc: 'Reach out to a recruiter directly' },
  { id: 'follow-up', label: 'Follow Up', desc: 'Follow up after applying or interviewing' },
  { id: 'informational', label: 'Informational Interview', desc: 'Request an informational interview' },
] as const

type MsgType = (typeof messageTypes)[number]['id']

export function LinkedInComposer() {
  const [msgType, setMsgType] = useState<MsgType>('connection')
  const [recipientName, setRecipientName] = useState('')
  const [recipientRole, setRecipientRole] = useState('')
  const [company, setCompany] = useState('')
  const [yourName, setYourName] = useState('')
  const [yourRole, setYourRole] = useState('Software Developer')
  const [targetRole, setTargetRole] = useState('')
  const [highlight, setHighlight] = useState('')
  const [result, setResult] = useState<LinkedInMessageResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const reqIdRef = useRef(0)

  const handleGenerate = async () => {
    if (!recipientName.trim() || !company.trim() || !yourName.trim()) return
    const reqId = ++reqIdRef.current
    setLoading(true)
    setError(null)
    try {
      const res = await dataService.generateLinkedInMessage({
        messageType: msgType,
        recipientName: recipientName.trim(),
        recipientRole: recipientRole.trim(),
        company: company.trim(),
        yourName: yourName.trim(),
        yourRole: yourRole.trim(),
        targetRole: targetRole.trim(),
        highlight: highlight.trim(),
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

  const charCount = result?.content.length ?? 0
  const charLimit = result?.characterLimit ?? 300

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">LinkedIn Message Composer</h1>
        <p className="text-sm text-text-secondary mt-1">
          Generate professional LinkedIn messages for networking, referrals, and recruiter outreach.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Controls (2/5) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader title="Message Type" icon={<Linkedin size={18} />} />
            <div className="space-y-2">
              {messageTypes.map((mt) => (
                <button
                  key={mt.id}
                  onClick={() => {
                    setMsgType(mt.id)
                    setResult(null)
                    setError(null)
                  }}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    msgType === mt.id
                      ? 'border-accent-indigo bg-accent-indigo/10'
                      : 'border-border-subtle bg-bg-surface hover:bg-bg-surface2',
                  )}
                >
                  <p className={cn(
                    'text-sm font-semibold',
                    msgType === mt.id ? 'text-accent-indigo' : 'text-text-primary',
                  )}>
                    {mt.label}
                  </p>
                  <p className="text-xs text-text-muted mt-0.5">{mt.desc}</p>
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader title="Details" icon={<User size={18} />} />
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Recipient Name *</label>
                <input value={recipientName} onChange={(e) => setRecipientName(e.target.value)} placeholder="e.g. Sarah" className="input-field w-full" />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Recipient Role</label>
                <input value={recipientRole} onChange={(e) => setRecipientRole(e.target.value)} placeholder="e.g. Engineering Manager" className="input-field w-full" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-text-secondary mb-1.5 block flex items-center gap-1">
                    <Building2 size={11} /> Company *
                  </label>
                  <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Stripe" className="input-field w-full" />
                </div>
                <div>
                  <label className="text-xs font-medium text-text-secondary mb-1.5 block flex items-center gap-1">
                    <Briefcase size={11} /> Your Role
                  </label>
                  <input value={yourRole} onChange={(e) => setYourRole(e.target.value)} className="input-field w-full" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Your Name *</label>
                <input value={yourName} onChange={(e) => setYourName(e.target.value)} placeholder="e.g. Jordan" className="input-field w-full" />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Target Role (optional)</label>
                <input value={targetRole} onChange={(e) => setTargetRole(e.target.value)} placeholder="e.g. Senior Frontend Engineer" className="input-field w-full" />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary mb-1.5 block">Key Highlight (optional)</label>
                <textarea
                  value={highlight}
                  onChange={(e) => setHighlight(e.target.value)}
                  rows={2}
                  placeholder="e.g. 6 years of React and TypeScript experience"
                  className="input-field w-full resize-none"
                />
              </div>
              <button
                onClick={handleGenerate}
                disabled={!recipientName.trim() || !company.trim() || !yourName.trim() || loading}
                className="btn-primary w-full text-sm flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                {loading ? 'Generating...' : 'Generate Message'}
              </button>
            </div>
          </Card>
        </div>

        {/* Right: Preview (3/5) */}
        <div className="lg:col-span-3">
          <Card className="h-full">
            <CardHeader
              title="Message Preview"
              subtitle="LinkedIn message — ready to copy and send"
              icon={<Linkedin size={18} />}
              action={
                result && (
                  <button onClick={handleCopy} className="btn-secondary text-xs flex items-center gap-1.5">
                    <Copy size={14} />
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                )
              }
            />
            {loading ? (
              <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                  <Loader2 size={32} className="animate-spin text-accent-indigo mx-auto mb-4" />
                  <p className="text-sm text-text-muted">Generating message...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-accent-rose/10 flex items-center justify-center text-accent-rose mx-auto mb-4">
                    <AlertCircle size={32} />
                  </div>
                  <h3 className="text-sm font-semibold text-text-primary mb-1">Generation Failed</h3>
                  <p className="text-xs text-text-muted max-w-xs">{error}</p>
                </div>
              </div>
            ) : result ? (
              <>
                <div className="bg-bg-surface2 rounded-lg p-6 min-h-[400px]">
                  <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border-subtle">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-indigo to-accent-violet flex items-center justify-center text-white font-bold text-sm">
                      {recipientName[0] || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-text-primary">{recipientName}</p>
                      <p className="text-xs text-text-muted">{recipientRole || '—'} · {company}</p>
                    </div>
                  </div>
                  <textarea
                    value={result.content}
                    onChange={(e) => setResult({ ...result, content: e.target.value, characterCount: e.target.value.length })}
                    className="w-full bg-transparent text-sm text-text-primary leading-relaxed resize-none focus:outline-none min-h-[300px]"
                  />
                </div>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-text-muted">{charCount} characters</span>
                  <span className={cn(
                    'text-xs font-medium',
                    charCount <= charLimit ? 'text-accent-emerald' : 'text-accent-amber',
                  )}>
                    {charCount <= charLimit
                      ? `✓ Within ${charLimit}-char limit`
                      : `Exceeds ${charLimit}-char limit (use InMail)`}
                  </span>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-bg-surface2 flex items-center justify-center text-text-muted mx-auto mb-4">
                    <Linkedin size={32} />
                  </div>
                  <h3 className="text-sm font-semibold text-text-primary mb-1">No message yet</h3>
                  <p className="text-xs text-text-muted max-w-xs">
                    Fill in the details on the left and click Generate to create a LinkedIn message.
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
