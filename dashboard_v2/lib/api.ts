// API client for NeuroAd Pipeline Dashboard

import type { Creative, Campaign, Brand } from './types'

const API_BASE_URL = 'http://localhost:8080'

export async function fetchCampaigns(): Promise<Campaign[]> {
  const response = await fetch(`${API_BASE_URL}/api/campaigns`)
  if (!response.ok) {
    throw new Error(`Failed to fetch campaigns: ${response.statusText}`)
  }
  const campaignNames = await response.json()

  // Map campaign names to campaign objects with IDs
  return campaignNames.map((name: string) => ({
    id: name,
    name: name,
    brandId: name, // Use campaign name as brandId for now
    date: new Date().toISOString().split('T')[0]
  }))
}

export async function fetchCampaignScores(campaignName: string): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignName}/scores`)
  if (!response.ok) {
    throw new Error(`Failed to fetch scores: ${response.statusText}`)
  }
  return await response.json()
}

export async function fetchBrandReport(campaignName: string): Promise<{ content: string }> {
  const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignName}/brand`)
  if (!response.ok) {
    throw new Error(`Failed to fetch brand report: ${response.statusText}`)
  }
  return await response.json()
}

// Transform raw pipeline score data to Creative type
export function transformPipelineData(rawData: any[]): Creative[] {
  return rawData.map((item, index) => {
    const assetName = item.asset_name || item.asset?.split('/')?.pop() || `creative_${index}`
    const assetId = item.asset_path?.split('/')?.pop()?.replace('.mp4', '') || `creative_${index}`

    // Transform mirofish data - extract from llm_scores or direct object
    const mirofishNested = item.mirofish || {}
    const mirofishData = mirofishNested.llm_scores || mirofishNested
    const mirofishScore = mirofishData.social_score ?? mirofishData.positive_sentiment ?? 0

    // Transform clip data - check both direct and nested paths
    const clipNested = item.clip || {}
    const clipScore = clipNested.brand_consistency ?? clipNested.brand_match_score ?? 0

    // Transform vinet data - check both vinet and saliency objects
    const vinetData = item.vinet || item.saliency || {}
    const vinetScore = vinetData.mean_saliency ?? vinetData.brand_attention ?? 0

    // Transform tribe data - check both direct tribe object and composite.breakdown
    const tribeNested = item.tribe || {}
    const compositeBreakdown = item.composite?.breakdown || {}
    // Use composite.breakdown if available, fall back to tribe object
    const tribeData = compositeBreakdown.neural_engagement !== undefined ? compositeBreakdown : tribeNested
    const tribeScore = tribeData.neural_engagement ?? 0

    // Use composite.total_score if available, otherwise calculate weighted score
    // Overall = TRIBE 30% + MiroFish 40% + CLIP 15% + ViNet 15%
    let overallScore: number
    if (item.composite?.total_score !== undefined) {
      overallScore = item.composite.total_score
    } else {
      overallScore =
        tribeScore * 0.30 +
        mirofishScore * 0.40 +
        clipScore * 0.15 +
        vinetScore * 0.15
    }

    // Determine campaign_id from item or derive from asset_path
    const campaignId = item.campaign_id || item.campaignName || 'default'

    return {
      id: assetId,
      name: assetName,
      campaignId: campaignId,
      tribe: {
        neural_engagement: tribeData.neural_engagement ?? 0,
        emotional_impact: (tribeData.emotional_impact ?? tribeNested.emotional_impact ?? compositeBreakdown.emotional_impact) ?? 0,
        face_response: (tribeData.face_response ?? tribeNested.face_response ?? compositeBreakdown.facial_emotion) ?? 0,
        scene_response: (tribeData.scene_response ?? tribeNested.scene_response ?? 0) ?? 0,
        motion_response: (tribeData.motion_response ?? tribeNested.motion_response ?? 0) ?? 0,
        language_engagement: (tribeData.language_engagement ?? tribeNested.language_engagement ?? 0) ?? 0,
        temporal_peak: typeof tribeNested.temporal_peak === 'number' ? `${Math.round(tribeNested.temporal_peak)}/36` : '0/36',
        engagement_stability: (tribeData.engagement_stability ?? tribeNested.engagement_stability ?? 0) ?? 0,
      },
      mirofish: {
        positive_sentiment: mirofishData.positive_sentiment ?? 0,
        virality_score: mirofishData.virality_score ?? 0,
        controversy_risk: mirofishData.controversy_risk ?? 0,
        social_score: mirofishScore,
        grade: getGrade(mirofishScore),
        target_audience_match: mirofishData.target_audience_match ?? 0,
        emotional_resonance: mirofishData.emotional_resonance ?? 0,
        shareability: mirofishData.shareability ?? 0,
        brand_affinity: mirofishData.brand_affinity ?? 0,
      },
      clip: {
        brand_match_score: clipScore,
        top_label: clipNested.top_label ?? 'unknown',
        grade: getGrade(clipScore),
        visual_dimensions: {
          color_consistency: clipNested.color_consistency ?? 0,
          typography_match: clipNested.typography_match ?? 0,
          imagery_style: clipNested.imagery_style ?? 0,
          tone_alignment: clipNested.tone_alignment ?? 0,
          logo_visibility: clipNested.logo_visibility ?? 0,
        },
        labels: clipNested.labels ?? [],
      },
      vinet: {
        mean_saliency: vinetScore,
        center_bias: vinetData.center_bias ?? 0,
        product_attention: vinetData.product_attention ?? 0,
        brand_attention: vinetData.brand_attention ?? 0,
        cta_attention: vinetData.cta_attention ?? 0,
        temporal_variance: vinetData.temporal_variance ?? 0,
      },
      overall_score: overallScore,
    }
  })
}

function getGrade(score: number): string {
  if (score >= 0.85) return 'A'
  if (score >= 0.75) return 'B'
  if (score >= 0.65) return 'C'
  if (score >= 0.55) return 'D'
  return 'F'
}
