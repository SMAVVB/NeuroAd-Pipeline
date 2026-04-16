'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { MetricBar } from '@/components/metric-bar'
import { AIAnalysis } from '@/components/ai-analysis'
import { LargeScoreDisplay } from '@/components/score-badge'
import { useDashboard } from '@/lib/dashboard-context'
import { aiAnalysis } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'

function RadarChart({ dimensions }: { dimensions: Record<string, number> }) {
  const labels = Object.keys(dimensions)
  const values = Object.values(dimensions)
  const numPoints = labels.length
  const angleStep = (2 * Math.PI) / numPoints
  const size = 200
  const center = size / 2
  const maxRadius = 80

  // Generate points for the data polygon
  const dataPoints = values.map((value, i) => {
    const angle = i * angleStep - Math.PI / 2
    const radius = value * maxRadius
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    }
  })

  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z'

  // Generate grid circles
  const gridLevels = [0.25, 0.5, 0.75, 1]

  return (
    <div className="flex justify-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-64 h-64">
        {/* Grid circles */}
        {gridLevels.map((level) => (
          <circle
            key={level}
            cx={center}
            cy={center}
            r={maxRadius * level}
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            className="text-border"
          />
        ))}

        {/* Axis lines */}
        {labels.map((_, i) => {
          const angle = i * angleStep - Math.PI / 2
          const x2 = center + maxRadius * Math.cos(angle)
          const y2 = center + maxRadius * Math.sin(angle)
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x2}
              y2={y2}
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-border"
            />
          )
        })}

        {/* Data polygon */}
        <path
          d={dataPath}
          fill="currentColor"
          fillOpacity="0.2"
          stroke="currentColor"
          strokeWidth="2"
          className="text-indigo"
        />

        {/* Data points */}
        {dataPoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="4"
            className="fill-indigo"
          />
        ))}

        {/* Labels */}
        {labels.map((label, i) => {
          const angle = i * angleStep - Math.PI / 2
          const labelRadius = maxRadius + 25
          const x = center + labelRadius * Math.cos(angle)
          const y = center + labelRadius * Math.sin(angle)
          return (
            <text
              key={i}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-muted-foreground text-[8px]"
            >
              {label.replace(/_/g, ' ')}
            </text>
          )
        })}
      </svg>
    </div>
  )
}

function CLIPContent() {
  const { availableCreatives, selectedCreativeId, setSelectedCreativeId } = useDashboard()

  const selectedCreative = availableCreatives.find(c => c.id === selectedCreativeId) || availableCreatives[0]

  if (!selectedCreative) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
        Please select a campaign with creatives
      </div>
    )
  }

  return (
    <>
      <PageHeader 
        title="Brand Consistency Analysis" 
        description="Measuring visual alignment between your creative and established brand guidelines"
      />

      {/* Creative selector */}
      <Tabs value={selectedCreativeId || availableCreatives[0]?.id} onValueChange={setSelectedCreativeId} className="mb-6">
        <TabsList>
          {availableCreatives.map((creative) => (
            <TabsTrigger key={creative.id} value={creative.id} className="text-xs">
              {creative.name}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Brand Match Score */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Brand Match Score</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-8">
          <LargeScoreDisplay 
            score={selectedCreative.clip.brand_match_score} 
            grade={selectedCreative.clip.grade}
            label="Brand Consistency"
          />
          <Badge variant="secondary" className="mt-4">
            Top Label: {selectedCreative.clip.top_label}
          </Badge>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2 mb-6">
        {/* Radar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Visual Dimensions</CardTitle>
          </CardHeader>
          <CardContent>
            <RadarChart dimensions={selectedCreative.clip.visual_dimensions} />
          </CardContent>
        </Card>

        {/* Label Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Label Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedCreative.clip.labels.map((label) => (
              <MetricBar
                key={label.name}
                label={label.name}
                value={label.score}
                showPercentage
                colorClass={label.score >= 0.8 ? 'bg-emerald-500' : label.score >= 0.6 ? 'bg-indigo' : 'bg-amber-500'}
              />
            ))}
          </CardContent>
        </Card>
      </div>

      {/* AI Analysis */}
      <AIAnalysis {...aiAnalysis.clip} />
    </>
  )
}

export default function CLIPPage() {
  return (
    <DashboardLayout>
      <CLIPContent />
    </DashboardLayout>
  )
}
