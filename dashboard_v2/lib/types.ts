// Types for NeuroAd Pipeline Dashboard

export interface Campaign {
  id: string
  name: string
  brandId: string
  date: string
}

export interface Brand {
  id: string
  name: string
  logo: string
}

export interface Creative {
  id: string
  name: string
  campaignId: string
  tribe: {
    neural_engagement: number
    emotional_impact: number
    face_response: number
    scene_response: number
    motion_response: number
    language_engagement: number
    temporal_peak: string
    engagement_stability: number
  }
  mirofish: {
    positive_sentiment: number
    virality_score: number
    controversy_risk: number
    social_score: number
    grade: string
    target_audience_match: number
    emotional_resonance: number
    shareability: number
    brand_affinity: number
  }
  clip: {
    brand_match_score: number
    top_label: string
    grade: string
    visual_dimensions: {
      color_consistency: number
      typography_match: number
      imagery_style: number
      tone_alignment: number
      logo_visibility: number
    }
    labels: { name: string; score: number }[]
  }
  vinet: {
    mean_saliency: number
    center_bias: number
    product_attention: number
    brand_attention: number
    cta_attention: number
    temporal_variance: number
  }
  overall_score: number
}

export interface DashboardState {
  selectedBrandId: string | null
  selectedCampaignId: string | null
  selectedCreativeId: string | null
  availableCampaigns: Campaign[]
  availableCreatives: Creative[]
  isDarkMode: boolean
  loading: boolean
  error: string | null
}
