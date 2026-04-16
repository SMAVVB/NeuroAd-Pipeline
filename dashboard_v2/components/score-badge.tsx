'use client'

import { cn } from '@/lib/utils'

interface ScoreBadgeProps {
  score: number
  grade?: string
  size?: 'sm' | 'md' | 'lg'
  showGrade?: boolean
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
  if (score >= 0.6) return 'bg-blue-500/10 text-blue-600 border-blue-500/20'
  if (score >= 0.4) return 'bg-amber-500/10 text-amber-600 border-amber-500/20'
  return 'bg-red-500/10 text-red-600 border-red-500/20'
}

function getGradeFromScore(score: number): string {
  if (score >= 0.9) return 'A+'
  if (score >= 0.85) return 'A'
  if (score >= 0.8) return 'A-'
  if (score >= 0.75) return 'B+'
  if (score >= 0.7) return 'B'
  if (score >= 0.65) return 'B-'
  if (score >= 0.6) return 'C+'
  if (score >= 0.55) return 'C'
  if (score >= 0.5) return 'C-'
  if (score >= 0.4) return 'D'
  return 'F'
}

export function ScoreBadge({ score, grade, size = 'md', showGrade = true }: ScoreBadgeProps) {
  const displayGrade = grade || getGradeFromScore(score)
  const colorClass = getScoreColor(score)

  return (
    <div className={cn(
      "inline-flex items-center gap-2 rounded-md border font-mono",
      colorClass,
      size === 'sm' && 'px-2 py-1 text-xs',
      size === 'md' && 'px-3 py-1.5 text-sm',
      size === 'lg' && 'px-4 py-2 text-base'
    )}>
      <span className="font-semibold">{(score * 100).toFixed(0)}%</span>
      {showGrade && <span className="font-bold">{displayGrade}</span>}
    </div>
  )
}

export function LargeScoreDisplay({ 
  score, 
  grade, 
  label 
}: { 
  score: number
  grade?: string
  label?: string 
}) {
  const displayGrade = grade || getGradeFromScore(score)
  const colorClass = getScoreColor(score)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="font-mono text-5xl font-bold tracking-tight">
        {(score * 100).toFixed(0)}
      </div>
      <div className={cn(
        "px-3 py-1 rounded-md border text-sm font-bold",
        colorClass
      )}>
        {displayGrade}
      </div>
      {label && (
        <span className="text-sm text-muted-foreground">{label}</span>
      )}
    </div>
  )
}
