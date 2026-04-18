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

function AttentionHeatmap({ saliencyData }: { saliencyData: any }) {
  const meanSaliency = saliencyData?.mean_saliency ?? 0
  const hasData = meanSaliency > 0.01

  if (!hasData) {
    return (
      <div className="aspect-video bg-muted rounded-lg flex flex-col items-center justify-center text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-lg font-medium">No Attention Data Available</p>
        <p className="text-sm mt-2 max-w-md text-center">
          ViNet attention analysis requires manual review for this creative.
        </p>
      </div>
    )
  }

  // Real heatmap using saliency map if available
  const saliencyMapPath = saliencyData?.saliency_map_path
  const heatmapPath = saliencyData?.heatmap_png_path
  const overlayPath = saliencyData?.overlay_png_path

  // Use overlay image if available, otherwise create a simple visualization
  if (overlayPath) {
    const imageUrl = `/api/campaigns/${saliencyData?.asset_path?.split('/')[1] || 'apple_vs_samsung'}/scores/${saliencyData?.asset_name?.replace('.mp4', '')}/vinet/overlay`
    return (
      <div className="aspect-video bg-muted rounded-lg relative overflow-hidden">
        <img
          src={imageUrl}
          alt="Attention Heatmap"
          className="w-full h-full object-cover"
          onError={(e) => {
            // Fallback if image not available
            e.currentTarget.style.display = 'none'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-4 right-4 bg-background/80 backdrop-blur-sm px-3 py-1.5 rounded text-xs font-medium text-white">
          Attention Heatmap
        </div>
      </div>
    )
  }

  // Simple visualization based on mean_saliency value
  return (
    <div className="aspect-video bg-muted rounded-lg relative overflow-hidden">
      {/* Base layer */}
      <div className="absolute inset-0 bg-gradient-to-br from-muted to-muted-foreground/10" />

      {/* Heatmap spots based on saliency value */}
      <div className="absolute inset-0">
        <div
          className="absolute w-32 h-32 rounded-full bg-red-500/60 blur-xl"
          style={{
            top: '30%',
            left: '40%',
            opacity: Math.min(meanSaliency * 2, 0.8)
          }}
        />
        <div
          className="absolute w-24 h-24 rounded-full bg-orange-500/50 blur-xl"
          style={{
            top: '50%',
            left: '60%',
            opacity: Math.min(meanSaliency * 1.5, 0.6)
          }}
        />
        <div
          className="absolute w-20 h-20 rounded-full bg-yellow-500/40 blur-xl"
          style={{
            top: '40%',
            left: '25%',
            opacity: Math.min(meanSaliency, 0.5)
          }}
        />
        <div
          className="absolute w-16 h-16 rounded-full bg-amber-500/30 blur-lg"
          style={{
            top: '65%',
            left: '45%',
            opacity: Math.min(meanSaliency * 0.8, 0.4)
          }}
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

  // Use mean_saliency as the main attention score
  const attentionScore = selectedCreative.vinet.mean_saliency
  const hasData = attentionScore > 0.01

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
          <AttentionHeatmap saliencyData={selectedCreative.vinet} />
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

      {/* Main Attention Score Display */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Attention Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="text-center md:text-left">
              <p className="text-sm text-muted-foreground mb-1">Mean Attention Score</p>
              <p className={`text-5xl font-mono font-semibold ${hasData ? 'text-foreground' : 'text-amber-500'}`}>
                {(attentionScore * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {hasData
                  ? 'Visual attention analysis completed successfully'
                  : 'Insufficient visual attention data - manual review recommended'}
              </p>
            </div>
            <div className="flex-1 w-full md:w-auto">
              <div className="space-y-2">
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
            </div>
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
