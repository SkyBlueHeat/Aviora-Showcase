import { cn } from '@/lib/utils'

interface ScoreCircleProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

export function ScoreCircle({ score, size = 'md', label }: ScoreCircleProps) {
  const radius = size === 'lg' ? 36 : size === 'sm' ? 20 : 28
  const strokeWidth = size === 'lg' ? 5 : size === 'sm' ? 3 : 4
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  const color =
    score >= 85 ? '#34D399' : score >= 70 ? '#22D3EE' : score >= 50 ? '#FBBF24' : '#F43F5E'

  const dims = size === 'lg' ? 'w-24 h-24' : size === 'sm' ? 'w-14 h-14' : 'w-20 h-20'
  const fontSize = size === 'lg' ? 'text-2xl' : size === 'sm' ? 'text-sm' : 'text-lg'

  return (
    <div className={cn('relative flex items-center justify-center', dims)}>
      <svg className="absolute inset-0 -rotate-90" viewBox={`0 0 ${radius * 2 + strokeWidth * 2} ${radius * 2 + strokeWidth * 2}`}>
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          fill="none"
          stroke="#1E2735"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="relative flex flex-col items-center">
        <span className={cn('font-bold', fontSize)} style={{ color }}>
          {score}
        </span>
        {label && <span className="text-2xs text-text-muted mt-0.5">{label}</span>}
      </div>
    </div>
  )
}
