'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { MetricBar } from '@/components/metric-bar'
import { AIAnalysis } from '@/components/ai-analysis'
import dynamic from 'next/dynamic'
import { useDashboard } from '@/lib/dashboard-context'
import { aiAnalysis } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import { ChevronDown, Activity, Zap } from 'lucide-react'
import { useState } from 'react'

const BrainViewer = dynamic(() => import('@/components/brain-viewer').then(m => ({ default: m.BrainViewer })), { ssr: false })

const brainRegions = [
  { id: 'temporal', name: 'Temporal Lobe', function: 'Face Response', x: 75, y: 55 },
  { id: 'occipital', name: 'Occipital Lobe', function: 'Scene & Motion', x: 85, y: 70 },
  { id: 'frontal', name: 'Frontal Lobe', function: 'Language & Engagement', x: 30, y: 35 },
  { id: 'limbic', name: 'Limbic System', function: 'Emotional Impact', x: 50, y: 60 },
]

function getRegionColor(score: number): string {
  if (score >= 0.2) return 'fill-emerald-500'
  if (score >= 0.18) return 'fill-amber-500'
  return 'fill-red-500'
}

function TRIBEContent() {
  const { availableCreatives, selectedCreativeId, setSelectedCreativeId } = useDashboard()
  const [isExplainerOpen, setIsExplainerOpen] = useState(false)

  const selectedCreative = availableCreatives.find(c => c.id === selectedCreativeId) || availableCreatives[0]

  if (!selectedCreative) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
        Please select a campaign with creatives
      </div>
    )
  }

  const metrics = [
    { label: 'Neural Engagement', value: selectedCreative.tribe.neural_engagement },
    { label: 'Emotional Impact', value: selectedCreative.tribe.emotional_impact },
    { label: 'Face Response', value: selectedCreative.tribe.face_response },
    { label: 'Scene Response', value: selectedCreative.tribe.scene_response },
    { label: 'Motion Response', value: selectedCreative.tribe.motion_response },
    { label: 'Language Engagement', value: selectedCreative.tribe.language_engagement },
  ]

  const regionScores: Record<string, number> = {
    temporal: selectedCreative.tribe.face_response,
    occipital: (selectedCreative.tribe.scene_response + selectedCreative.tribe.motion_response) / 2,
    frontal: (selectedCreative.tribe.language_engagement + selectedCreative.tribe.neural_engagement) / 2,
    limbic: selectedCreative.tribe.emotional_impact,
  }

  return (
    <>
      <PageHeader 
        title="Neural Engagement Analysis" 
        description="fMRI-based models scoring brain region responses to your creative"
      />

      {/* What is TRIBE? */}
      <Collapsible open={isExplainerOpen} onOpenChange={setIsExplainerOpen} className="mb-6">
        <Card>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
              <CardTitle className="text-base flex items-center justify-between">
                <span>What is TRIBE?</span>
                <ChevronDown className={`h-4 w-4 transition-transform ${isExplainerOpen ? 'rotate-180' : ''}`} />
              </CardTitle>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="pt-0">
              <p className="text-muted-foreground mb-6">
                TRIBE v2 uses fMRI-based models to score how different brain regions respond to your creative.
                Each metric represents neural activity patterns associated with specific cognitive and emotional processes.
              </p>

              {/* Brain Region Map */}
              <div className="relative w-full max-w-md mx-auto aspect-square">
                <svg viewBox="0 0 100 100" className="w-full h-full">
                  {/* Simple brain outline */}
                  <path
                    d="M50 10 C20 10 10 30 10 50 C10 75 25 90 50 90 C75 90 90 75 90 50 C90 30 80 10 50 10"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1"
                    className="text-border"
                  />
                  {/* Brain region indicators */}
                  {brainRegions.map((region) => (
                    <g key={region.id}>
                      <circle
                        cx={region.x}
                        cy={region.y}
                        r="8"
                        className={`${getRegionColor(regionScores[region.id])} opacity-80`}
                      />
                      <circle
                        cx={region.x}
                        cy={region.y}
                        r="4"
                        className="fill-background"
                      />
                    </g>
                  ))}
                </svg>
                {/* Labels */}
                <div className="absolute inset-0">
                  {brainRegions.map((region) => (
                    <div
                      key={region.id}
                      className="absolute text-xs transform -translate-x-1/2"
                      style={{ left: `${region.x}%`, top: `${region.y + 12}%` }}
                    >
                      <span className="block text-center font-medium">{region.function}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-center gap-6 mt-6 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-muted-foreground">Above benchmark (&gt;0.20)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span className="text-muted-foreground">At benchmark (0.18)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="text-muted-foreground">Below benchmark</span>
                </div>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* 3D Brain Viewer */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">3D Brain Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <BrainViewer tribeScores={selectedCreative.tribe} size="md" />
          <div className="mt-4 flex justify-center gap-6 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="text-muted-foreground">High (≥0.20)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <span className="text-muted-foreground">Medium (0.18)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-muted-foreground">Low (&lt;0.18)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Scores */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Live Scores</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Creative selector tabs */}
          <Tabs value={selectedCreativeId || availableCreatives[0]?.id} onValueChange={setSelectedCreativeId} className="mb-6">
            <TabsList>
              {availableCreatives.map((creative) => (
                <TabsTrigger key={creative.id} value={creative.id} className="text-xs">
                  {creative.name}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {/* Metric bars */}
          <div className="grid gap-4 md:grid-cols-2">
            {metrics.map((metric) => (
              <MetricBar
                key={metric.label}
                label={metric.label}
                value={metric.value}
                maxValue={0.3}
                benchmark={0.18}
                colorClass={metric.value >= 0.18 ? 'bg-indigo' : 'bg-amber-500'}
              />
            ))}
          </div>

          {/* Key indicators */}
          <div className="mt-6 pt-6 border-t flex flex-col sm:flex-row gap-4">
            <Card className="flex-1 bg-muted/50">
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-3">
                  <Activity className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Engagement Stability</p>
                    <p className="text-2xl font-mono font-semibold">{selectedCreative.tribe.engagement_stability.toFixed(3)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="flex-1 bg-muted/50">
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-3">
                  <Zap className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Temporal Peak</p>
                    <p className="text-2xl font-mono font-semibold">{selectedCreative.tribe.temporal_peak}</p>
                    <p className="text-xs text-muted-foreground">Strong recency effect</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* AI Analysis */}
      <AIAnalysis {...aiAnalysis.tribe} />
    </>
  )
}

export default function TRIBEPage() {
  return (
    <DashboardLayout>
      <TRIBEContent />
    </DashboardLayout>
  )
}
