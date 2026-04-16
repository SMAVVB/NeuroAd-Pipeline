'use client'

import { cn } from '@/lib/utils'

interface MetricBarProps {
  label: string
  value: number
  maxValue?: number
  benchmark?: number
  showPercentage?: boolean
  colorClass?: string
  size?: 'sm' | 'md' | 'lg'
}

export function MetricBar({
  label,
  value,
  maxValue = 1,
  benchmark,
  showPercentage = false,
  colorClass = 'bg-indigo',
  size = 'md',
}: MetricBarProps) {
  const percentage = (value / maxValue) * 100
  const benchmarkPosition = benchmark ? (benchmark / maxValue) * 100 : null
  const displayValue = showPercentage ? `${Math.round(value * 100)}%` : value.toFixed(3)

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className={cn(
          "text-muted-foreground",
          size === 'sm' && 'text-xs',
          size === 'md' && 'text-sm',
          size === 'lg' && 'text-base'
        )}>
          {label}
        </span>
        <span className={cn(
          "font-mono font-medium",
          size === 'sm' && 'text-xs',
          size === 'md' && 'text-sm',
          size === 'lg' && 'text-base'
        )}>
          {displayValue}
        </span>
      </div>
      <div className="relative">
        <div className={cn(
          "w-full bg-muted rounded-full overflow-hidden",
          size === 'sm' && 'h-1.5',
          size === 'md' && 'h-2',
          size === 'lg' && 'h-3'
        )}>
          <div
            className={cn("h-full rounded-full transition-all duration-500", colorClass)}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
        {benchmarkPosition !== null && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-muted-foreground/50"
            style={{ left: `${benchmarkPosition}%` }}
          />
        )}
      </div>
    </div>
  )
}
