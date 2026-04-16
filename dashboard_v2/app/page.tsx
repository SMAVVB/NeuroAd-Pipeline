'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { useDashboard } from '@/lib/dashboard-context'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { Trophy, AlertTriangle, Brain, Fish, Palette, Eye, ChevronUp, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'

type SortKey = 'name' | 'tribe' | 'mirofish' | 'clip' | 'vinet' | 'overall'
type SortDirection = 'asc' | 'desc'

function OverviewContent() {
  const { availableCreatives, selectedCampaign, loading, error } = useDashboard()
  const [sortKey, setSortKey] = useState<SortKey>('overall')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  // Show loading state
  if (loading) {
    return (
      <div className="p-8">
        <PageHeader title="Overview" />
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-48" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Skeleton className="h-10 w-full" />
                    {[1, 2, 3, 4, 5].map(i => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <Skeleton className="h-5 w-32" />
                </CardHeader>
                <CardContent className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="flex gap-3">
                      <Skeleton className="h-4 w-4" />
                      <Skeleton className="h-4 flex-1" />
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <Skeleton className="h-5 w-32 mb-3" />
                  <Skeleton className="h-6 w-48 mb-2" />
                  <Skeleton className="h-4 w-32" />
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] p-8 text-center">
        <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
        <h2 className="text-xl font-semibold mb-2">Error Loading Data</h2>
        <p className="text-muted-foreground mb-6 max-w-md">{error}</p>
        <p className="text-sm text-muted-foreground">
          Make sure the FastAPI backend is running on <code className="font-mono bg-muted px-1 py-0.5 rounded">http://localhost:8080</code>
        </p>
      </div>
    )
  }

  if (!selectedCampaign) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
        Please select a campaign from the sidebar
      </div>
    )
  }

  const getScore = (creative: typeof availableCreatives[0], key: SortKey): number => {
    switch (key) {
      case 'tribe': return creative.tribe.neural_engagement
      case 'mirofish': return creative.mirofish.social_score
      case 'clip': return creative.clip.brand_match_score
      case 'vinet': return creative.vinet.mean_saliency
      case 'overall': return creative.overall_score
      default: return 0
    }
  }

  const sortedCreatives = [...availableCreatives].sort((a, b) => {
    if (sortKey === 'name') {
      return sortDirection === 'asc' 
        ? a.name.localeCompare(b.name)
        : b.name.localeCompare(a.name)
    }
    const aScore = getScore(a, sortKey)
    const bScore = getScore(b, sortKey)
    return sortDirection === 'asc' ? aScore - bScore : bScore - aScore
  })

  const bestCreative = availableCreatives.reduce((best, current) => 
    current.overall_score > best.overall_score ? current : best
  , availableCreatives[0])

  const getColumnBest = (key: SortKey) => {
    if (key === 'name' || key === 'overall') return null
    return availableCreatives.reduce((best, current) => 
      getScore(current, key) > getScore(best, key) ? current : best
    , availableCreatives[0])
  }

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDirection('desc')
    }
  }

  const SortIcon = ({ columnKey }: { columnKey: SortKey }) => {
    if (sortKey !== columnKey) return null
    return sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
  }

  // Find weakest module for the best creative
  const moduleScores = [
    { name: 'TRIBE', score: bestCreative?.tribe.neural_engagement || 0 },
    { name: 'MiroFish', score: bestCreative?.mirofish.social_score || 0 },
    { name: 'CLIP', score: bestCreative?.clip.brand_match_score || 0 },
    { name: 'ViNet', score: bestCreative?.vinet.mean_saliency || 0 },
  ]
  const weakestModule = moduleScores.reduce((weakest, current) => 
    current.score < weakest.score ? current : weakest
  , moduleScores[0])

  const recommendations = [
    `Deploy "${bestCreative?.name}" as primary creative for maximum impact`,
    `Improve ${weakestModule.name} metrics for balanced performance`,
    'Consider A/B testing top 2 creatives for conversion optimization',
  ]

  return (
    <>
      <PageHeader title="Overview" />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Creative Performance Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Creative Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead 
                      className="cursor-pointer hover:text-foreground"
                      onClick={() => toggleSort('name')}
                    >
                      <div className="flex items-center gap-1">
                        Creative <SortIcon columnKey="name" />
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:text-foreground text-right"
                      onClick={() => toggleSort('tribe')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        TRIBE <SortIcon columnKey="tribe" />
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:text-foreground text-right"
                      onClick={() => toggleSort('mirofish')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        MiroFish <SortIcon columnKey="mirofish" />
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:text-foreground text-right"
                      onClick={() => toggleSort('clip')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        CLIP <SortIcon columnKey="clip" />
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:text-foreground text-right"
                      onClick={() => toggleSort('vinet')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        ViNet <SortIcon columnKey="vinet" />
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:text-foreground text-right"
                      onClick={() => toggleSort('overall')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Overall <SortIcon columnKey="overall" />
                      </div>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedCreatives.map((creative) => (
                    <TableRow key={creative.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          {creative.id === bestCreative?.id && (
                            <Trophy className="h-4 w-4 text-amber-500" />
                          )}
                          {creative.name}
                        </div>
                      </TableCell>
                      <TableCell className={cn(
                        "text-right font-mono",
                        getColumnBest('tribe')?.id === creative.id && "text-emerald-600 font-semibold"
                      )}>
                        {creative.tribe.neural_engagement.toFixed(3)}
                      </TableCell>
                      <TableCell className={cn(
                        "text-right font-mono",
                        getColumnBest('mirofish')?.id === creative.id && "text-emerald-600 font-semibold"
                      )}>
                        {creative.mirofish.social_score.toFixed(2)}
                      </TableCell>
                      <TableCell className={cn(
                        "text-right font-mono",
                        getColumnBest('clip')?.id === creative.id && "text-emerald-600 font-semibold"
                      )}>
                        {creative.clip.brand_match_score.toFixed(3)}
                      </TableCell>
                      <TableCell className={cn(
                        "text-right font-mono",
                        getColumnBest('vinet')?.id === creative.id && "text-emerald-600 font-semibold"
                      )}>
                        {creative.vinet.mean_saliency.toFixed(3)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant={creative.overall_score >= 0.8 ? 'default' : 'secondary'} className="font-mono">
                          {(creative.overall_score * 100).toFixed(0)}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Quick Insights Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Key Recommendations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recommendations.map((rec, i) => (
                <div key={i} className="flex gap-3">
                  <span className="font-mono text-sm font-semibold text-indigo shrink-0">{i + 1}.</span>
                  <p className="text-sm text-muted-foreground">{rec}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="bg-emerald-500/5 border-emerald-500/20">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-2">
                <Trophy className="h-5 w-5 text-emerald-600" />
                <span className="text-sm font-medium text-emerald-600">Best Performer</span>
              </div>
              <p className="font-semibold">{bestCreative?.name}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Overall score: <span className="font-mono">{((bestCreative?.overall_score || 0) * 100).toFixed(0)}%</span>
              </p>
            </CardContent>
          </Card>

          <Card className="bg-amber-500/5 border-amber-500/20">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <span className="text-sm font-medium text-amber-600">Weakest Module</span>
              </div>
              <p className="font-semibold">{weakestModule.name}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Needs attention in top creative
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Module Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mt-6">
        <ModuleSummaryCard
          icon={Brain}
          title="TRIBE Neural"
          description="fMRI-based neural engagement scoring"
          topScore={Math.max(...availableCreatives.map(c => c.tribe.neural_engagement))}
        />
        <ModuleSummaryCard
          icon={Fish}
          title="MiroFish Social"
          description="AI-simulated social media response"
          topScore={Math.max(...availableCreatives.map(c => c.mirofish.social_score))}
        />
        <ModuleSummaryCard
          icon={Palette}
          title="CLIP Brand"
          description="Visual brand consistency analysis"
          topScore={Math.max(...availableCreatives.map(c => c.clip.brand_match_score))}
        />
        <ModuleSummaryCard
          icon={Eye}
          title="ViNet Attention"
          description="Visual saliency & attention mapping"
          topScore={Math.max(...availableCreatives.map(c => c.vinet.mean_saliency))}
        />
      </div>
    </>
  )
}

function ModuleSummaryCard({
  icon: Icon,
  title,
  description,
  topScore,
}: {
  icon: typeof Brain
  title: string
  description: string
  topScore: number
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded bg-muted flex items-center justify-center">
            <Icon className="h-4 w-4" />
          </div>
          <span className="font-medium">{title}</span>
        </div>
        <p className="text-xs text-muted-foreground mb-3">{description}</p>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-mono font-semibold">{topScore.toFixed(3)}</span>
          <span className="text-xs text-muted-foreground">top score</span>
        </div>
      </CardContent>
    </Card>
  )
}

export default function OverviewPage() {
  return (
    <DashboardLayout>
      <OverviewContent />
    </DashboardLayout>
  )
}
