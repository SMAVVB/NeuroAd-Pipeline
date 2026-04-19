'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Campaign, Creative, Brand } from './types'
import { fetchCampaigns, fetchCampaignScores, transformPipelineData } from './api'

interface DashboardContextType {
  selectedBrandId: string | null
  selectedCampaignId: string | null
  selectedCreativeId: string | null
  setSelectedBrandId: (id: string | null) => void
  setSelectedCampaignId: (id: string | null) => void
  setSelectedCreativeId: (id: string | null) => void
  selectedBrand: Brand | undefined
  selectedCampaign: Campaign | undefined
  selectedCreative: Creative | undefined
  availableCampaigns: Campaign[]
  availableCreatives: Creative[]
  isDarkMode: boolean
  toggleDarkMode: () => void
  loading: boolean
  error: string | null
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

// Default brands for fallback
const brands: Brand[] = [
  { id: 'apple', name: 'Apple', logo: '🍎' },
  { id: 'yfood', name: 'yfood', logo: '🥤' },
  { id: 'redbull', name: 'Red Bull', logo: '🐂' },
]

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [selectedBrandId, setSelectedBrandId] = useState<string | null>(null)
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null)
  const [selectedCreativeId, setSelectedCreativeId] = useState<string | null>(null)
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [availableCampaigns, setAvailableCampaigns] = useState<Campaign[]>([])
  const [availableCreatives, setAvailableCreatives] = useState<Creative[]>([])

  // Fetch campaigns on mount
  useEffect(() => {
    const loadCampaigns = async () => {
      try {
        setLoading(true)
        const campaigns = await fetchCampaigns()
        setAvailableCampaigns(campaigns)

        // Set first campaign as default if none selected
        if (campaigns.length > 0 && !selectedCampaignId) {
          setSelectedCampaignId(campaigns[0].id)
        }
      } catch (err) {
        setError('Failed to load campaigns. Make sure the FastAPI backend is running on port 8080.')
        console.error('Error loading campaigns:', err)
      } finally {
        setLoading(false)
      }
    }

    loadCampaigns()
  }, [])

  // Fetch scores when campaign changes
  useEffect(() => {
    const loadScores = async () => {
      if (!selectedCampaignId) {
        setAvailableCreatives([])
        return
      }

      try {
        setLoading(true)
        const rawData = await fetchCampaignScores(selectedCampaignId)
        const transformed = transformPipelineData(rawData)
        setAvailableCreatives(transformed)

        // Set first creative as default if none selected
        if (transformed.length > 0 && !selectedCreativeId) {
          setSelectedCreativeId(transformed[0].id)
        }
      } catch (err) {
        setError('Failed to load campaign scores.')
        console.error('Error loading scores:', err)
      } finally {
        setLoading(false)
      }
    }

    loadScores()
  }, [selectedCampaignId])

  const selectedBrand = brands.find(b => b.id === selectedBrandId)
  const selectedCampaign = availableCampaigns.find(c => c.id === selectedCampaignId)
  const selectedCreative = availableCreatives.find(c => c.id === selectedCreativeId)

  const toggleDarkMode = () => {
    setIsDarkMode(prev => {
      const newValue = !prev
      if (newValue) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      return newValue
    })
  }

  return (
    <DashboardContext.Provider
      value={{
        selectedBrandId,
        selectedCampaignId,
        selectedCreativeId,
        setSelectedBrandId,
        setSelectedCampaignId,
        setSelectedCreativeId,
        selectedBrand,
        selectedCampaign,
        selectedCreative,
        availableCampaigns,
        availableCreatives,
        isDarkMode,
        toggleDarkMode,
        loading,
        error,
      }}
    >
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const context = useContext(DashboardContext)
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider')
  }
  return context
}
