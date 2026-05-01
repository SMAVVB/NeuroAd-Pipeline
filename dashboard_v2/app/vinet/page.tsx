'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { MetricBar } from '@/components/metric-bar'
import { AIAnalysis } from '@/components/ai-analysis'
import { useDashboard } from '@/lib/dashboard-context'
import { aiAnalysis } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertCircle } from 'lucide-react'
import { useState, useEffect } from 'react'
import { toast } from 'sonner'

function AttentionHeatmap({ saliencyData }: { saliencyData: any }) {
  const meanSaliency = saliencyData?.mean_saliency ?? 0
  const hasData = meanSaliency > 0.01
  const [imageLoaded, setImageLoaded] = useState(false)

  // Extract asset name from asset_path or use saliencyData
  const getAssetName = () => {
    if (saliencyData?.asset_name) return saliencyData.asset_name
    if (saliencyData?.asset_path) {
      const parts = saliencyData.asset_path.split('/')
      const lastPart = parts[parts.length - 1]
      return lastPart.replace('.mp4', '')
    }
    return 'apple_iphone17pro_ultimate'
  }

  const assetName = getAssetName()

  // Extract campaign name from asset_path
  const getCampaignName = () => {
    if (saliencyData?.asset_path) {
      const parts = saliencyData.asset_path.split('/')
      const campaignIdx = parts.indexOf('campaigns')
      if (campaignIdx >= 0 && campaignIdx + 1 < parts.length) {
        return parts[campaignIdx + 1]
      }
    }
    return 'apple_vs_samsung'
  }

  const campaignName = getCampaignName()

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

  // Use overlay image if available, otherwise use saliency heatmap
  if (overlayPath || heatmapPath) {
    const imageUrl = `/api/campaigns/${campaignName}/assets/${assetName}/heatmap`
    const heatmapType = overlayPath ? 'overlay' : 'saliency'

    return (
      <div className="aspect-video bg-muted rounded-lg relative overflow-hidden">
        <img
          src={`${imageUrl}?heatmap_type=${heatmapType}`}
          alt="Attention Heatmap"
          className={`w-full h-full object-cover ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setImageLoaded(true)}
          onError={(e) => {
            // Fallback if image not available
            e.currentTarget.style.display = 'none'
          }}
        />
        {!imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-foreground" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-4 right-4 bg-background/80 backdrop-blur-sm px-3 py-1.5 rounded text-xs font-medium text-white">
          Attention Heatmap
        </div>
      </div>
    )
  }

  // Simple visualization based on mean_saliency value (fallback)
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

      {/* Attention Metrics - Product, Brand, CTA as MetricBars */}
      <div className="space-y-3 mb-6">
        <p className="text-sm font-medium text-muted-foreground">Attention Scores</p>
        {selectedCreative.vinet.product_attention > 0 && (
          <MetricBar
            label="Product Attention"
            value={selectedCreative.vinet.product_attention}
            showPercentage
            colorClass={selectedCreative.vinet.product_attention > 0.5 ? 'bg-emerald-500' : 'bg-indigo'}
          />
        )}
        {selectedCreative.vinet.brand_attention > 0 && (
          <MetricBar
            label="Brand Attention"
            value={selectedCreative.vinet.brand_attention}
            showPercentage
            colorClass={selectedCreative.vinet.brand_attention > 0.5 ? 'bg-emerald-500' : 'bg-indigo'}
          />
        )}
        {selectedCreative.vinet.cta_attention > 0 && (
          <MetricBar
            label="CTA Attention"
            value={selectedCreative.vinet.cta_attention}
            showPercentage
            colorClass={selectedCreative.vinet.cta_attention > 0.5 ? 'bg-emerald-500' : 'bg-indigo'}
          />
        )}
        {selectedCreative.vinet.product_attention === 0 &&
         selectedCreative.vinet.brand_attention === 0 &&
         selectedCreative.vinet.cta_attention === 0 && (
          <div className="text-xs text-muted-foreground italic">
            No detailed attention scores available
          </div>
        )}
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
