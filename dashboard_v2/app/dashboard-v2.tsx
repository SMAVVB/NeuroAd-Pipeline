'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface Creative {
  id: string
  name: string
  tribe: {
    neural_engagement: number
    emotional_impact: number
    face_response: number
    scene_response: number
    motion_response: number
    language_engagement: number
  }
  emotion: {
    dominant_emotion: string
    emotional_valence: number
    face_coverage: number
  }
  clip: {
    brand_match_score: number
    top_label: string
    top_label_score: number
  }
  mirofish: {
    social_score: number
    positive_sentiment: number
    negative_sentiment: number
  }
  vinet: {
    mean_saliency: number
  }
  overall: {
    overall_score: number
    grade: string
  }
  overall_score: number
}

interface DashboardState {
  availableCreatives: Creative[]
  selectedCampaign: string | null
  loading: boolean
  error: string | null
  campaigns: string[]
}

interface DashboardContextType extends DashboardState {
  selectCampaign: (name: string) => void
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DashboardState>({
    availableCreatives: [],
    selectedCampaign: null,
    loading: false,
    error: null,
    campaigns: [],
  })

  const fetchCampaigns = async () => {
    try {
      const res = await fetch('/api/campaigns')
      const data = await res.json()
      setState(prev => ({ ...prev, campaigns: Array.isArray(data) ? data : [] }))
    } catch {
      setState(prev => ({ ...prev, campaigns: ['nike_summer_26'] }))
    }
  }

  const fetchScores = async (campaignName: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    try {
      const res = await fetch(`/api/campaigns/${encodeURIComponent(campaignName)}/scores`)
      const data = await res.json()

      if (res.ok && Array.isArray(data)) {
        const creatives = data.map((item: any) => ({
          id: item.tribe?.asset_path || item.asset_path || item.name || '',
          name: item.tribe?.asset_name || item.asset_name || item.name || 'Unknown',
          tribe: item.tribe || item,
          emotion: item.emotion || item,
          clip: item.clip || item,
          mirofish: item.mirofish || item,
          vinet: item.saliency || item,
          overall: item.composite || item,
          overall_score: item.composite?.total_score ?? item.overall_score ?? item.tribe?.neural_engagement ?? 0,
        }))
        setState(prev => ({ ...prev, availableCreatives: creatives, loading: false }))
      } else {
        setState(prev => ({ ...prev, availableCreatives: [], loading: false }))
      }
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to fetch scores',
      }))
    }
  }

  const selectCampaign = async (name: string) => {
    setState(prev => ({ ...prev, selectedCampaign: name, loading: true }))
    await fetchScores(name)
  }

  useEffect(() => {
    fetchCampaigns()
    setState(prev => ({ ...prev, selectedCampaign: prev.campaigns[0] }))
  }, [])

  useEffect(() => {
    if (state.selectedCampaign) {
      fetchScores(state.selectedCampaign)
    }
  }, [state.selectedCampaign])

  return (
    <DashboardContext.Provider value={{ ...state, selectCampaign }}>
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider')
  return ctx
}
