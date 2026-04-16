'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { MetricBar } from '@/components/metric-bar'
import { AIAnalysis } from '@/components/ai-analysis'
import { useDashboard } from '@/lib/dashboard-context'
import { aiAnalysis } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertCircle, Package, Bookmark, MousePointer } from 'lucide-react'

function HeatmapPlaceholder({ hasData }: { hasData: boolean }) {
  if (!hasData) {
    return (
      <div className="aspect-video bg-muted rounded-lg flex flex-col items-center justify-center text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-lg font-medium">No Attention Data Available</p>
        <p className="text-sm mt-2 max-w-md text-center">
          ViNet attention scores are at 0% for this creative. This may indicate the creative 
          lacks distinct visual anchors or the analysis requires manual review.
        </p>
      </div>
    )
  }

  // Simulated heatmap visualization
  return (
    <div className="aspect-video bg-muted rounded-lg relative overflow-hidden">
      {/* Base layer */}
      <div className="absolute inset-0 bg-gradient-to-br from-muted to-muted-foreground/10" />
      
      {/* Heatmap spots */}
      <div className="absolute inset-0">
        <div 
          className="absolute w-32 h-32 rounded-full bg-red-500/60 blur-xl"
          style={{ top: '30%', left: '40%' }}
        />
        <div 
          className="absolute w-24 h-24 rounded-full bg-orange-500/50 blur-xl"
          style={{ top: '50%', left: '60%' }}
        />
        <div 
          className="absolute w-20 h-20 rounded-full bg-yellow-500/40 blur-xl"
          style={{ top: '40%', left: '25%' }}
        />
        <div 
          className="absolute w-16 h-16 rounded-full bg-amber-500/30 blur-lg"
          style={{ top: '65%', left: '45%' }}
        />
      </div>

      {/* Overlay label */}
      <div className="absolute bottom-4 right-4 bg-background/80 backdrop-blur-sm px-3 py-1.5 rounded text-xs font-medium">
        Attention Heatmap
      </div>
    </div>
  )
}

function AttentionMetricCard({
  icon: Icon,
  label,
  value,
  hasData,
}: {
  icon: typeof Package
  label: string
  value: number
  hasData: boolean
}) {
  const displayValue = hasData ? `${(value * 100).toFixed(0)}%` : '0%'
  const isZero = value === 0

  return (
    <Card className={isZero ? 'border-amber-500/30 bg-amber-500/5' : ''}>
      <CardContent className="pt-6">
        <div className="flex items-center gap-3 mb-2">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isZero ? 'bg-amber-500/10' : 'bg-muted'}`}>
            <Icon className={`h-5 w-5 ${isZero ? 'text-amber-500' : 'text-muted-foreground'}`} />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className={`text-3xl font-mono font-semibold ${isZero ? 'text-amber-500' : ''}`}>
              {displayValue}
            </p>
          </div>
        </div>
        {isZero && (
          <p className="text-xs text-amber-600 mt-2">Needs attention optimization</p>
        )}
      </CardContent>
    </Card>
  )
}

function ViNetContent() {
  const { availableCreatives, selectedCreativeId, setSelectedCreativeId } = useDashboard()

  const selectedCreative = availableCreatives.find(c => c.id === selectedCreativeId) || availableCreatives[0]

  if (!selectedCreative) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
        Please select a campaign with creatives
      </div>
    )
  }

  const hasData = selectedCreative.vinet.mean_saliency > 0.1

  return (
    <>
      <PageHeader 
        title="Visual Attention Mapping" 
        description="Eye-tracking simulation revealing where viewers focus their attention"
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

      {/* Heatmap Display */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Attention Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <HeatmapPlaceholder hasData={hasData} />
        </CardContent>
      </Card>

      {/* Attention Metrics */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <AttentionMetricCard
          icon={Package}
          label="Product Attention"
          value={selectedCreative.vinet.product_attention}
          hasData={hasData}
        />
        <AttentionMetricCard
          icon={Bookmark}
          label="Brand Attention"
          value={selectedCreative.vinet.brand_attention}
          hasData={hasData}
        />
        <AttentionMetricCard
          icon={MousePointer}
          label="CTA Attention"
          value={selectedCreative.vinet.cta_attention}
          hasData={hasData}
        />
      </div>

      {/* Additional Metrics */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Additional Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <MetricBar
              label="Center Bias"
              value={selectedCreative.vinet.center_bias}
              showPercentage
              colorClass={selectedCreative.vinet.center_bias > 0.8 ? 'bg-amber-500' : 'bg-indigo'}
            />
            <MetricBar
              label="Temporal Variance"
              value={selectedCreative.vinet.temporal_variance}
              showPercentage
              colorClass={selectedCreative.vinet.temporal_variance > 0.3 ? 'bg-amber-500' : 'bg-emerald-500'}
            />
          </div>
          <div className="mt-4 p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Mean Saliency: </span>
              <span className="font-mono">{selectedCreative.vinet.mean_saliency.toFixed(3)}</span>
              {selectedCreative.vinet.mean_saliency < 0.1 && (
                <span className="ml-2 text-amber-600">— Low saliency indicates weak visual anchors</span>
              )}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* AI Analysis */}
      <AIAnalysis {...aiAnalysis.vinet} />
    </>
  )
}

export default function ViNetPage() {
  return (
    <DashboardLayout>
      <ViNetContent />
    </DashboardLayout>
  )
}
