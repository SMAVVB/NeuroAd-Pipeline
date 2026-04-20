'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { useDashboard } from '@/lib/dashboard-context'
import { aiAnalysis } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Trophy, Download, FileJson, Medal, CheckCircle, Lightbulb } from 'lucide-react'

// Helper to format creative name: "apple_pay_outrun" -> "Apple Pay Outrun"
function formatCreativeName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
}

// Module types for scoring
type ModuleScore = {
  name: string
  score: number
  label: string
}

// Module types mapping
const moduleTypes = ['tribe', 'mirofish', 'clip', 'vinet'] as const
type ModuleType = typeof moduleTypes[number]

// Helper to get module scores from a creative
function getModuleScores(creative: any): ModuleScore[] {
  return [
    { name: 'tribe', score: creative.tribe.neural_engagement, label: 'TRIBE' },
    { name: 'mirofish', score: creative.mirofish.social_score, label: 'MiroFish' },
    { name: 'clip', score: creative.clip.brand_match_score, label: 'CLIP' },
    { name: 'vinet', score: creative.vinet.mean_saliency, label: 'ViNet' },
  ]
}

// Helper to get the best and weakest modules
function getBestWeakestModules(scores: ModuleScore[]): { best: ModuleScore; weakest: ModuleScore } {
  const sorted = [...scores].sort((a, b) => b.score - a.score)
  return { best: sorted[0], weakest: sorted[sorted.length - 1] }
}

// Generate dynamic executive summary based on actual creative data
function generateExecutiveSummary(creatives: any[]): string {
  if (creatives.length === 0) return 'No creative data available for analysis.'

  const ranked = [...creatives].sort((a, b) => b.overall_score - a.overall_score)
  const winner = ranked[0]
  const scores = getModuleScores(winner)
  const { best, weakest } = getBestWeakestModules(scores)

  // Format score as percentage
  const formatScore = (s: number) => Math.round(s * 100).toString()

  // Format creative name: "apple_pay_outrun" -> "Apple Pay Outrun"
  const formattedWinnerName = winner.name.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())

  return `${formattedWinnerName} leads with ${formatScore(winner.overall_score)}% overall score. Strongest module: ${best.label} (${formatScore(best.score)}%). Weakest module: ${weakest.label} (${formatScore(weakest.score)}%).`
}

function ReportContent() {
  const { availableCreatives, selectedCampaign } = useDashboard()

  if (!selectedCampaign || availableCreatives.length === 0) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
        Please select a campaign with creatives
      </div>
    )
  }

  // Sort creatives by overall score
  const rankedCreatives = [...availableCreatives].sort((a, b) => b.overall_score - a.overall_score)
  const winner = rankedCreatives[0]

  // Generate dynamic executive summary
  const executiveSummary = generateExecutiveSummary(availableCreatives)

  const handleExportPDF = () => {
    alert('PDF export would be generated here with full report data')
  }

  const handleExportJSON = () => {
    const data = {
      campaign: selectedCampaign,
      creatives: rankedCreatives,
      executiveSummary,
      analysis: aiAnalysis.consolidated,
      exportedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `neuroadpipeline-report-${selectedCampaign.id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <PageHeader 
        title="Creative Performance Report" 
        description="Comprehensive analysis and ranking of all campaign creatives"
      />

      {/* Creative Ranking */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Medal className="h-5 w-5" />
            Creative Ranking
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {rankedCreatives.map((creative, index) => {
              const isWinner = index === 0
              const rank = index + 1

              return (
                <div
                  key={creative.id}
                  className={cn(
                    "p-4 rounded-lg border transition-colors",
                    isWinner ? "bg-amber-500/5 border-amber-500/30" : "bg-muted/30"
                  )}
                >
                  <div className="flex items-start gap-4">
                    {/* Rank badge */}
                    <div className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold shrink-0",
                      isWinner ? "bg-amber-500 text-white" : "bg-muted text-muted-foreground"
                    )}>
                      {isWinner ? <Trophy className="h-5 w-5" /> : rank}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold">{formatCreativeName(creative.name)}</h3>
                        {isWinner && (
                          <Badge className="bg-amber-500 hover:bg-amber-600">Winner</Badge>
                        )}
                      </div>

                      {/* Module scores grid */}
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                        <div>
                          <span className="text-muted-foreground block text-xs">TRIBE</span>
                          <span className="font-mono">{creative.tribe.neural_engagement.toFixed(3)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-xs">MiroFish</span>
                          <span className="font-mono">{creative.mirofish.social_score.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-xs">CLIP</span>
                          <span className="font-mono">{creative.clip.brand_match_score.toFixed(3)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-xs">ViNet</span>
                          <span className="font-mono">{creative.vinet.mean_saliency.toFixed(3)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-xs">Overall</span>
                          <span className="font-mono font-semibold text-indigo">
                            {(creative.overall_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Consolidated AI Analysis */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-indigo flex items-center justify-center">
              <span className="text-indigo-foreground text-xs font-bold">AI</span>
            </div>
            Consolidated Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Executive Summary */}
          <div>
            <h4 className="font-medium mb-2">Executive Summary</h4>
            <p className="text-muted-foreground leading-relaxed">
              {executiveSummary}
            </p>
          </div>

          {/* Cross-Module Insights */}
          <div>
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-500" />
              Cross-Module Insights
            </h4>
            <ul className="space-y-2">
              {aiAnalysis.consolidated.crossModuleInsights.map((insight, i) => (
                <li key={i} className="flex gap-3 text-sm text-muted-foreground">
                  <span className="text-emerald-500 shrink-0">•</span>
                  {insight}
                </li>
              ))}
            </ul>
          </div>

          {/* Final Recommendation */}
          <div className="p-4 bg-indigo/5 border border-indigo/20 rounded-lg">
            <h4 className="font-medium mb-2 flex items-center gap-2 text-indigo">
              <Lightbulb className="h-4 w-4" />
              Final Recommendation
            </h4>
            <p className="text-sm leading-relaxed">
              {aiAnalysis.consolidated.finalRecommendation}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Export Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button onClick={handleExportPDF} className="gap-2">
          <Download className="h-4 w-4" />
          Export PDF Report
        </Button>
        <Button variant="outline" onClick={handleExportJSON} className="gap-2">
          <FileJson className="h-4 w-4" />
          Export JSON Data
        </Button>
      </div>
    </>
  )
}

export default function ReportPage() {
  return (
    <DashboardLayout>
      <ReportContent />
    </DashboardLayout>
  )
}
