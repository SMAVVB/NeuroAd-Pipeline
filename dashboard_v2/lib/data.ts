// Fallback data for NeuroAd Pipeline
// API data from FastAPI backend (http://localhost:8080) takes precedence

import type { Creative, Campaign, Brand } from './types'

// Fallback brands - used when API is unavailable
export const brands: Brand[] = [
  { id: 'apple', name: 'Apple', logo: '🍎' },
  { id: 'yfood', name: 'yfood', logo: '🥤' },
  { id: 'redbull', name: 'Red Bull', logo: '🐂' },
]

// Fallback campaigns - used when API is unavailable
export const campaigns: Campaign[] = [
  { id: 'apple-samsung-q1', name: 'Apple vs Samsung Q1 2026', brandId: 'apple', date: '2026-03-15' },
  { id: 'yfood-campaign', name: 'yfood Spring Launch', brandId: 'yfood', date: '2026-02-20' },
]

// Fallback creatives - used when API is unavailable
export const creatives: Creative[] = []

export const brandIntelligence = {
  apple: {
    name: 'Apple Inc.',
    foundingYear: 1976,
    headquarters: 'Cupertino, California',
    industry: 'Consumer Electronics & Technology',
    size: 'Enterprise (164,000+ employees)',
    markets: ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East'],
    competitors: ['Samsung', 'Google', 'Microsoft', 'Huawei', 'Sony'],
    subIndustries: ['Smartphones', 'Computers', 'Wearables', 'Services', 'Software'],
    lastResearchDate: '2026-03-10',
    stormReportUrl: '#',
    historicalPeriods: [
      { year: '1976-1985', label: 'Founding Era' },
      { year: '1985-1997', label: 'Wilderness Years' },
      { year: '1997-2011', label: 'Jobs Renaissance' },
      { year: '2011-Present', label: 'Cook Era' },
    ],
  },
}

export const aiAnalysis = {
  tribe: {
    summary: 'The creative demonstrates strong neural engagement patterns with particularly high face response scores, indicating effective use of human elements. The temporal peak occurring late in the sequence (31/36) suggests a strong recency effect that will aid brand recall.',
    strengths: [
      'Exceptional face response (0.217) indicates strong human connection',
      'High engagement stability (0.986) shows consistent viewer attention',
      'Strong neural engagement above benchmark threshold',
    ],
    weaknesses: [
      'Language engagement slightly below optimal levels',
      'Emotional impact could be enhanced with more dynamic storytelling',
    ],
    recommendations: [
      'Consider adding more emotionally charged moments earlier in the sequence',
      'Optimize language elements for better cognitive processing',
      'Maintain the strong human presence that drives face response',
    ],
  },
  mirofish: {
    summary: 'Social simulation indicates strong positive reception with high virality potential. The creative resonates well with target demographics and shows excellent brand affinity scores.',
    strengths: [
      'High positive sentiment (85%) predicts favorable audience reception',
      'Strong brand affinity suggests effective brand integration',
      'Low controversy risk minimizes potential backlash',
    ],
    weaknesses: [
      'Virality score (0.70) has room for improvement',
      'Shareability could be enhanced with more "meme-able" moments',
    ],
    recommendations: [
      'Add shareable moments that encourage social interaction',
      'Consider including user-generated content elements',
      'Leverage emotional peaks for maximum social impact',
    ],
  },
  clip: {
    summary: 'Brand consistency analysis reveals moderate alignment with established brand guidelines. The cinematic storytelling approach is on-brand but logo visibility needs attention.',
    strengths: [
      'Strong imagery style alignment with brand aesthetic',
      'Effective use of cinematic storytelling techniques',
      'Color palette maintains brand consistency',
    ],
    weaknesses: [
      'Logo visibility significantly below recommended levels',
      'Typography match could be strengthened',
    ],
    recommendations: [
      'Increase logo presence without disrupting creative flow',
      'Ensure typography aligns with brand guidelines',
      'Consider brand element placement optimization',
    ],
  },
  vinet: {
    summary: 'Attention mapping reveals high center bias but limited saliency distribution. The current creative may benefit from more strategic placement of key brand elements.',
    strengths: [
      'Strong center focus ensures primary message delivery',
      'Consistent attention patterns across viewing duration',
    ],
    weaknesses: [
      'Product attention scores at 0% indicate visibility issues',
      'Brand element placement not optimized for attention capture',
      'CTA visibility needs significant improvement',
    ],
    recommendations: [
      'Reposition product elements to high-saliency regions',
      'Add visual anchors to guide attention to brand elements',
      'Implement contrast techniques to highlight CTA',
    ],
  },
  consolidated: {
    executiveSummary: 'Analysis of the Apple vs Samsung Q1 2026 campaign reveals "Apple Pay Outrun" as the strongest performer across all neural, social, brand, and attention metrics. This creative demonstrates superior emotional impact and social virality potential while maintaining brand consistency.',
    crossModuleInsights: [
      'Neural engagement correlates strongly with social sentiment across all creatives',
      'Higher face response scores consistently predict better emotional resonance',
      'Brand consistency gaps in CLIP analysis may explain lower ViNet attention scores',
      'Motion response peaks align with predicted viral moments in MiroFish simulation',
    ],
    finalRecommendation: 'Deploy "Apple Pay Outrun" as the primary creative for maximum campaign impact. Its combination of high emotional engagement, social virality potential, and brand affinity makes it the optimal choice for the target audience.',
  },
}
