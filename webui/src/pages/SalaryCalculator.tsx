import { useState } from 'react'
import { Card, CardHeader } from '@/components/Card'
import {
  Calculator,
  DollarSign,
  TrendingUp,
  PiggyBank,
  Percent,
} from 'lucide-react'

export function SalaryCalculator() {
  const [base, setBase] = useState(180000)
  const [bonusPct, setBonusPct] = useState(10)
  const [equity, setEquity] = useState(20000)
  const [signing, setSigning] = useState(10000)
  const [benefits, setBenefits] = useState(12000)
  const [taxPct, setTaxPct] = useState(28)

  const annualBonus = (base * bonusPct) / 100
  const totalCash = base + annualBonus + signing
  const totalComp = totalCash + equity + benefits
  const netAnnual = totalComp * (1 - taxPct / 100)
  const netMonthly = netAnnual / 12

  const fmt = (n: number) => `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`

  const breakdown = [
    { label: 'Base Salary', value: base, color: 'text-accent-indigo' },
    { label: 'Annual Bonus', value: annualBonus, color: 'text-accent-cyan' },
    { label: 'Equity (annualized)', value: equity, color: 'text-accent-violet' },
    { label: 'Signing Bonus', value: signing, color: 'text-accent-amber' },
    { label: 'Benefits', value: benefits, color: 'text-accent-emerald' },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Salary Calculator</h1>
        <p className="text-sm text-text-secondary mt-1">
          Calculate total compensation, tax implications, and monthly net income.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inputs */}
        <Card>
          <CardHeader title="Compensation Details" icon={<Calculator size={18} />} />
          <div className="space-y-4">
            <SliderInput label="Base Salary" value={base} onChange={setBase} min={50000} max={400000} step={5000} format={fmt} />
            <SliderInput label="Bonus %" value={bonusPct} onChange={setBonusPct} min={0} max={30} step={1} format={(v) => `${v}%`} />
            <SliderInput label="Equity (annual)" value={equity} onChange={setEquity} min={0} max={100000} step={5000} format={fmt} />
            <SliderInput label="Signing Bonus" value={signing} onChange={setSigning} min={0} max={50000} step={1000} format={fmt} />
            <SliderInput label="Benefits Value" value={benefits} onChange={setBenefits} min={0} max={30000} step={1000} format={fmt} />
            <SliderInput label="Tax Bracket" value={taxPct} onChange={setTaxPct} min={10} max={45} step={1} format={(v) => `${v}%`} />
          </div>
        </Card>

        {/* Results */}
        <div className="space-y-4">
          {/* Total Comp */}
          <Card className="bg-gradient-to-br from-accent-indigo/10 to-accent-violet/5 border-accent-indigo/20">
            <div className="text-center py-4">
              <p className="text-xs font-medium text-text-secondary mb-1">Total Annual Compensation</p>
              <p className="text-4xl font-bold text-text-primary">{fmt(totalComp)}</p>
              <div className="flex items-center justify-center gap-4 mt-3">
                <div>
                  <p className="text-2xs text-text-muted">Net Annual</p>
                  <p className="text-sm font-bold text-accent-emerald">{fmt(netAnnual)}</p>
                </div>
                <div className="w-px h-8 bg-border-subtle" />
                <div>
                  <p className="text-2xs text-text-muted">Net Monthly</p>
                  <p className="text-sm font-bold text-accent-cyan">{fmt(netMonthly)}</p>
                </div>
              </div>
            </div>
          </Card>

          {/* Breakdown */}
          <Card>
            <CardHeader title="Breakdown" icon={<DollarSign size={18} />} />
            <div className="space-y-3">
              {breakdown.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">{item.label}</span>
                  <span className={`text-sm font-semibold ${item.color}`}>{fmt(item.value)}</span>
                </div>
              ))}
              <div className="pt-3 border-t border-border-subtle space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-text-primary">Total Cash</span>
                  <span className="text-sm font-bold text-text-primary">{fmt(totalCash)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
                    <Percent size={14} className="text-accent-rose" /> Tax ({taxPct}%)
                  </span>
                  <span className="text-sm font-bold text-accent-rose">-{fmt(totalComp - netAnnual)}</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Counter strategy */}
          <Card>
            <CardHeader
              title="Counter Strategy"
              subtitle="AI-powered negotiation recommendation"
              icon={<TrendingUp size={18} />}
            />
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <PiggyBank size={16} className="text-accent-emerald shrink-0 mt-0.5" />
                <p className="text-sm text-text-secondary">
                  Counter with <span className="font-bold text-text-primary">{fmt(Math.round(base * 1.12))}</span> base — you have strong leverage with multiple ongoing interviews.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <TrendingUp size={16} className="text-accent-cyan shrink-0 mt-0.5" />
                <p className="text-sm text-text-secondary">
                  Ask for <span className="font-bold text-text-primary">15% higher equity</span> vesting — standard for senior roles at this stage.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

function SliderInput({
  label,
  value,
  onChange,
  min,
  max,
  step,
  format,
}: {
  label: string
  value: number
  onChange: (v: number) => void
  min: number
  max: number
  step: number
  format: (v: number) => string
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs font-medium text-text-secondary">{label}</label>
        <span className="text-sm font-bold text-text-primary">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-bg-surface2 rounded-full appearance-none cursor-pointer accent-accent-indigo"
      />
    </div>
  )
}
