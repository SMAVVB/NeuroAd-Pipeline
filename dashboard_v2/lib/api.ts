// API client for NeuroAd Pipeline Dashboard

import type { Creative, Campaign, Brand } from './types'

const API_BASE_URL = ''

export async function fetchCampaigns(): Promise<Campaign[]> {
  const response = await fetch(`${API_BASE_URL}/api/campaigns`)
  if (!response.ok) {
    throw new Error(`Failed to fetch campaigns: ${response.statusText}`)
  }
  const campaignNames = await response.json()

  // Data already transformed by Next.js API route
  return Array.isArray(campaignNames) && typeof campaignNames[0] === 'object'
    ? campaignNames
    : campaignNames.map((name: string) => ({
        id: name,
        name: name,
        brandId: name,
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
    // Transform creative name: "apple_pay_outrun" -> "Apple Pay Outrun"
    const rawName = item.asset_name || item.asset?.split('/')?.pop() || `creative_${index}`
    const assetName = rawName.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
    const assetId = item.asset_path?.split('/')?.pop()?.replace('.mp4', '') || `creative_${index}`

    // Transform mirofish data - extract from llm_scores or direct object
    const mirofishNested = item.mirofish || {}
    const mirofishData = mirofishNested.llm_scores || mirofishNested

    // Transform clip data - use brand_match_score from clip scores
    const clipNested = item.clip || {}
    const clipScore = clipNested.brand_match_score ?? clipNested.brand_consistency ?? 0
    const topLabel = clipNested.top_label ?? 'unknown'
    const allScores = clipNested.all_scores || {}
    const labels = Object.entries(allScores).map(([name, score]) => ({ name, score: score as number }))

    // Transform vinet data - use mean_saliency as the main score
    const vinetData = item.vinet || item.saliency || {}
    const vinetScore = vinetData.mean_saliency ?? 0

    // Transform tribe data - read directly from item.tribe, NOT from composite.breakdown
    const tribeNested = item.tribe || {}
    const compositeBreakdown = item.composite?.breakdown || {}

    // Use composite.total_score if available, otherwise calculate weighted score
    // Overall = TRIBE 30% + MiroFish 40% + CLIP 15% + ViNet 15%
    let overallScore: number
    if (item.composite?.total_score !== undefined) {
      overallScore = item.composite.total_score
    } else {
      overallScore =
        (tribeNested.neural_engagement ?? 0) * 0.30 +
        (mirofishData.positive_sentiment ?? 0) * 0.40 +
        clipScore * 0.15 +
        vinetScore * 0.15
    }

    // Determine campaign_id from item or derive from asset_path
    const campaignId = item.campaign_id || item.campaignName || 'default'

    // Map tribe fields directly to Creative type
    // scene_response, motion_response, language_engagement come from item.tribe directly
    // composite.breakdown has: neural_engagement, emotional_impact, visual_attention, brand_consistency, social_sentiment, audio_engagement

    const neuralEngagement = tribeNested.neural_engagement ?? compositeBreakdown.neural_engagement ?? 0
    const emotionalImpact = tribeNested.emotional_impact ?? compositeBreakdown.emotional_impact ?? 0
    const facialEmotion = tribeNested.face_response ?? tribeNested.facial_emotion ?? 0
    const sceneResponse = tribeNested.scene_response ?? (compositeBreakdown.visual_attention ?? 0) * 0.6
    const motionResponse = tribeNested.motion_response ?? (compositeBreakdown.visual_attention ?? 0) * 0.4
    const languageEngagement = tribeNested.language_engagement ?? compositeBreakdown.audio_engagement ?? 0
    const socialSentiment = compositeBreakdown.social_sentiment ?? mirofishData.positive_sentiment ?? 0

    return {
      id: assetId,
      name: assetName,
      campaignId: campaignId,
      tribe: {
        neural_engagement: neuralEngagement,
        emotional_impact: emotionalImpact,
        face_response: facialEmotion,
        scene_response: sceneResponse,
        motion_response: motionResponse,
        language_engagement: languageEngagement,
        temporal_peak: tribeNested.temporal_peak && tribeNested.n_segments
          ? `${Math.round(tribeNested.temporal_peak)}/${tribeNested.n_segments}`
          : '0/36',
        engagement_stability: tribeNested.engagement_stability ?? compositeBreakdown.engagement_stability ?? 0.5,
      },
      mirofish: {
        positive_sentiment: mirofishData.positive_sentiment ?? 0,
        virality_score: mirofishData.virality_score ?? 0,
        controversy_risk: mirofishData.controversy_risk ?? 0,
        social_score: socialSentiment,
        grade: getGrade(socialSentiment),
        target_audience_match: mirofishData.target_audience_match ?? 0,
        emotional_resonance: mirofishData.emotional_resonance ?? 0,
        shareability: mirofishData.shareability ?? 0,
        brand_affinity: mirofishData.brand_affinity ?? 0,
      },
      clip: {
        brand_match_score: clipScore,
        top_label: topLabel,
        grade: getGrade(clipScore),
        visual_dimensions: {
          color_consistency: allScores['vibrant colorful energy'] ?? Object.values(allScores)[0] ?? 0,
          typography_match: allScores['sleek minimalist design'] ?? Object.values(allScores)[1] ?? 0,
          imagery_style: allScores['cinematic storytelling'] ?? Object.values(allScores)[2] ?? 0,
          tone_alignment: allScores['emotional lifestyle'] ?? Object.values(allScores)[3] ?? 0,
          logo_visibility: allScores['feature demonstration'] ?? Object.values(allScores)[4] ?? 0,
        },
        labels: labels.length > 0 ? labels : [{ name: topLabel, score: clipScore }],
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
