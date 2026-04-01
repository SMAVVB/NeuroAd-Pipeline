import React from 'react'

function ScoreCard({ label, value, unit = '', tooltip, color = 'accent' }) {
  const colorClasses = {
    accent: 'text-accent',
    success: 'text-success',
    warning: 'text-warning',
    danger: 'text-danger',
    secondary: 'text-secondary',
  }
  
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-secondary">{label}</span>
        {tooltip && (
          <span className="tooltip" data-tooltip={tooltip}>
            <span className="text-secondary">ℹ️</span>
          </span>
        )}
      </div>
      <div className={`text-3xl font-bold ${colorClasses[color] || colorClasses.accent}`}>
        {value}
        {unit && <span className="text-lg ml-1">{unit}</span>}
      </div>
    </div>
  )
}

export default ScoreCard
