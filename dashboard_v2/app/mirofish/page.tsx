'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { MetricBar } from '@/components/metric-bar'
import { AIAnalysis } from '@/components/ai-analysis'
import { useDashboard } from '@/lib/dashboard-context'
import { aiAnalysis } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { ChevronDown } from 'lucide-react'
import { useState, useEffect } from 'react'
import MiroFishGraph, { type GraphData } from '@/components/mirofish-graph'

// Generate agent graph data from MiroFish sentiment data
function generateAgentGraphData(mirofishData: any): GraphData {
  const numAgents = 18 // Generate 18 agent nodes

  const nodes: any[] = []
  for (let i = 0; i < numAgents; i++) {
    const agentNum = i + 1
    const agentId = `agent-${agentNum.toString().padStart(2, '0')}`

    // Generate agent-specific sentiment values centered around MiroFish scores
    const sentimentVariance = (Math.random() - 0.5) * 0.3
    const controversyVariance = (Math.random() - 0.5) * 0.2

    const agentPositiveSentiment = Math.min(1, Math.max(0, mirofishData.positive_sentiment + sentimentVariance))
    const agentControversyRisk = Math.min(1, Math.max(0, mirofishData.controversy_risk + controversyVariance))
    const agentViralityScore = Math.min(1, Math.max(0, mirofishData.virality_score + (Math.random() - 0.5) * 0.2))

    nodes.push({
      id: agentId,
      name: `Agent_${agentNum.toString().padStart(2, '0')}`,
      positiveSentiment: agentPositiveSentiment,
      controversyRisk: agentControversyRisk,
      viralityScore: agentViralityScore,
    })
  }

  // Create edges: connect approximately 30% of nodes randomly
  const edges: any[] = []
  const edgeSet = new Set<string>()

  nodes.forEach((sourceNode, sourceIndex) => {
    const numConnections = 2 + Math.floor(Math.random() * 3)

    for (let i = 0; i < numConnections; i++) {
      const targetIndex = Math.floor(Math.random() * numAgents)
      if (targetIndex !== sourceIndex) {
        const targetNode = nodes[targetIndex]
        const edgeKey = [sourceNode.id, targetNode.id].sort().join('-')

        if (!edgeSet.has(edgeKey)) {
          edgeSet.add(edgeKey)
          edges.push({
            source: sourceNode,
            target: targetNode,
          })
        }
      }
    }
  })

  return { nodes, edges }
}

function GaugeChart({ value, label, max = 1 }: { value: number; label: string; max?: number }) {
  const percentage = (value / max) * 100
  const rotation = (percentage / 100) * 180 - 90

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-20 overflow-hidden">
        <svg viewBox="0 0 100 50" className="w-full h-full">
          {/* Background arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-muted"
          />
          {/* Value arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeDasharray={`${percentage * 1.26} 126`}
            className="text-indigo"
          />
          {/* Needle */}
          <line
            x1="50"
            y1="50"
            x2="50"
            y2="18"
            stroke="currentColor"
            strokeWidth="2"
            className="text-foreground origin-bottom"
            style={{ transform: `rotate(${rotation}deg)`, transformOrigin: '50px 50px' }}
          />
          <circle cx="50" cy="50" r="4" className="fill-foreground" />
        </svg>
      </div>
      <div className="text-center mt-2">
        <p className="text-2xl font-mono font-semibold">{(value * 100).toFixed(0)}%</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  )
}

function MiroFishContent() {
  const { availableCreatives, selectedCreativeId, setSelectedCreativeId } = useDashboard()
  const [isExplainerOpen, setIsExplainerOpen] = useState(false)
  const [graphData, setGraphData] = useState<GraphData | undefined>(undefined)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [hasGraphError, setHasGraphError] = useState(false)

  const selectedCreative = availableCreatives.find(c => c.id === selectedCreativeId) || availableCreatives[0]

  if (!selectedCreative) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
        Please select a campaign with creatives
      </div>
    )
  }

  // Fetch MiroFish graph data
  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        setLoadingGraph(true)
        setHasGraphError(false)
        const response = await fetch(`/api/campaigns/${selectedCreative.name}/mirofish`)
        if (response.ok) {
          const data = await response.json()
          setGraphData(data)
        } else {
          // FastAPI returned error - use generated agent data
          setHasGraphError(true)
          setGraphData(generateAgentGraphData(selectedCreative.mirofish))
        }
      } catch (error) {
        console.error('Failed to fetch graph data:', error)
        // Network error - use generated agent data
        setHasGraphError(true)
        setGraphData(generateAgentGraphData(selectedCreative.mirofish))
      } finally {
        setLoadingGraph(false)
      }
    }

    fetchGraphData()
  }, [selectedCreative.name])

  const sentimentMetrics = [
    { label: 'Target Audience Match', value: selectedCreative.mirofish.target_audience_match },
    { label: 'Emotional Resonance', value: selectedCreative.mirofish.emotional_resonance },
    { label: 'Shareability', value: selectedCreative.mirofish.shareability },
    { label: 'Brand Affinity', value: selectedCreative.mirofish.brand_affinity },
  ]

  return (
    <>
      <PageHeader
        title="Social Simulation Analysis"
        description="AI agent network simulating real social media reactions to your creative"
      />

      {/* What is MiroFish? */}
      <Collapsible open={isExplainerOpen} onOpenChange={setIsExplainerOpen} className="mb-6">
        <Card>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
              <CardTitle className="text-base flex items-center justify-between">
                <span>What is MiroFish?</span>
                <ChevronDown className={`h-4 w-4 transition-transform ${isExplainerOpen ? 'rotate-180' : ''}`} />
              </CardTitle>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="pt-0">
              <p className="text-muted-foreground">
                MiroFish simulates how real social media users react to your creative using an AI agent network.
                Each agent represents a user persona with unique preferences, behaviors, and social connections.
                The simulation predicts virality, sentiment, and engagement patterns before your creative goes live.
              </p>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

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

      {/* MiroFish Graph Visualization */}
      <Card className="mb-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Entity Relationship Graph</CardTitle>
          {hasGraphError && (
            <span className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded-full">
              Fallback Data
            </span>
          )}
        </CardHeader>
        <CardContent className="h-[600px]">
          <MiroFishGraph graphData={graphData} loading={loadingGraph} height={600} />
        </CardContent>
      </Card>

      {/* Sentiment Metrics - Preserved from original */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Sentiment Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Gauge charts */}
          <div className="flex justify-center gap-12 mb-8">
            <GaugeChart value={selectedCreative.mirofish.virality_score} label="Virality Score" />
            <GaugeChart value={selectedCreative.mirofish.positive_sentiment} label="Positive Sentiment" />
          </div>

          {/* Metric bars */}
          <div className="grid gap-4 md:grid-cols-2">
            {sentimentMetrics.map((metric) => (
              <MetricBar
                key={metric.label}
                label={metric.label}
                value={metric.value}
                showPercentage
                colorClass={metric.value >= 0.7 ? 'bg-indigo' : 'bg-amber-500'}
              />
            ))}
          </div>

          {/* Grade badge */}
          <div className="mt-6 pt-6 border-t flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Social Score</p>
              <p className="text-3xl font-mono font-semibold">{(selectedCreative.mirofish.social_score * 100).toFixed(0)}%</p>
            </div>
            <div className="px-4 py-2 bg-indigo/10 rounded-lg border border-indigo/20">
              <span className="text-2xl font-bold text-indigo">{selectedCreative.mirofish.grade}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Analysis */}
      <AIAnalysis {...aiAnalysis.mirofish} />
    </>
  )
}

export default function MiroFishPage() {
  return (
    <DashboardLayout>
      <MiroFishContent />
    </DashboardLayout>
  )
}
