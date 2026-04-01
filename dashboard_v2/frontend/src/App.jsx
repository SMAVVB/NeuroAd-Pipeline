import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import SaliencyPage from './pages/SaliencyPage.jsx'
import TribePage from './pages/TribePage.jsx'
import ClipPage from './pages/ClipPage.jsx'
import EmotionPage from './pages/EmotionPage.jsx'
import MiroFishPage from './pages/MiroFishPage.jsx'
import ReportPage from './pages/ReportPage.jsx'

function App() {
  const [campaigns, setCampaigns] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState('')
  const [assets, setAssets] = useState([])
  const [selectedAsset, setSelectedAsset] = useState('')
  const [loading, setLoading] = useState(true)
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    // Load campaigns
    fetchCampaigns()
    
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    document.documentElement.dataset.theme = savedTheme
  }, [])

  const fetchCampaigns = async () => {
    try {
      const response = await fetch('/api/campaigns')
      const data = await response.json()
      setCampaigns(data)
      
      if (data.length > 0) {
        setSelectedCampaign(data[0].name)
        setAssets(data[0].assets)
        if (data[0].assets.length > 0) {
          setSelectedAsset(data[0].assets[0])
        }
      }
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCampaignChange = async (campaignName) => {
    setSelectedCampaign(campaignName)
    setLoading(true)
    
    try {
      const response = await fetch(`/api/campaign/${campaignName}`)
      const data = await response.json()
      setAssets(data.assets || [])
      
      if (data.assets && data.assets.length > 0) {
        setSelectedAsset(data.assets[0])
      }
    } catch (error) {
      console.error('Failed to fetch assets:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAssetChange = (assetName) => {
    setSelectedAsset(assetName)
  }

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.dataset.theme = newTheme
  }

  if (loading && campaigns.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="skeleton w-16 h-16 rounded-full mx-auto mb-4"></div>
          <p className="text-secondary">Loading NeuroAd Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-subtle border-r border-border flex flex-col">
          <div className="p-6 border-b border-border">
            <h1 className="text-xl font-bold bg-gradient-to-r from-accent to-indigo-500 bg-clip-text text-transparent">
              NeuroAd Intelligence
            </h1>
            <p className="text-sm text-secondary mt-1">Campaign Analysis Dashboard</p>
          </div>
          
          <div className="p-4 flex flex-col gap-4">
            {/* Campaign Selector */}
            <div>
              <label className="text-sm font-semibold text-secondary mb-2 block">
                Campaign
              </label>
              <select
                value={selectedCampaign}
                onChange={(e) => handleCampaignChange(e.target.value)}
                className="w-full bg-card border border-border rounded p-2 text-sm focus:outline-none focus:border-accent"
                disabled={loading}
              >
                {campaigns.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Asset Selector */}
            <div>
              <label className="text-sm font-semibold text-secondary mb-2 block">
                Asset
              </label>
              <select
                value={selectedAsset}
                onChange={(e) => handleAssetChange(e.target.value)}
                className="w-full bg-card border border-border rounded p-2 text-sm focus:outline-none focus:border-accent"
                disabled={loading || assets.length === 0}
              >
                {assets.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="w-full bg-card border border-border rounded p-2 text-sm flex items-center justify-center gap-2 hover:bg-border transition-colors"
            >
              {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
            </button>
          </div>
          
          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            <NavLink to="/saliency" label="Saliency" />
            <NavLink to="/tribe" label="TRIBE Brain" />
            <NavLink to="/clip" label="CLIP Brand" />
            <NavLink to="/emotion" label="Emotion" />
            <NavLink to="/mirofish" label="MiroFish" />
            <NavLink to="/report" label="Report" />
          </nav>
          
          <div className="p-4 border-t border-border">
            <div className="text-xs text-secondary text-center">
              v2.0.0 • FastAPI + React
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="flex-1 overflow-y-auto bg-primary">
          <div className="p-8 max-w-7xl mx-auto">
            <Routes>
              <Route
                path="/saliency"
                element={<SaliencyPage campaign={selectedCampaign} asset={selectedAsset} />}
              />
              <Route
                path="/tribe"
                element={<TribePage campaign={selectedCampaign} asset={selectedAsset} />}
              />
              <Route
                path="/clip"
                element={<ClipPage campaign={selectedCampaign} asset={selectedAsset} />}
              />
              <Route
                path="/emotion"
                element={<EmotionPage campaign={selectedCampaign} asset={selectedAsset} />}
              />
              <Route
                path="/mirofish"
                element={<MiroFishPage campaign={selectedCampaign} asset={selectedAsset} />}
              />
              <Route
                path="/report"
                element={<ReportPage campaign={selectedCampaign} />}
              />
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  )
}

function NavLink({ to, label }) {
  const location = useLocation()
  const isActive = location.pathname === to
  
  return (
    <Link
      to={to}
      className={`block p-3 rounded-lg text-sm font-medium transition-colors ${
        isActive
          ? 'bg-accent/10 text-accent'
          : 'text-secondary hover:bg-border hover:text-primary'
      }`}
    >
      {label}
    </Link>
  )
}

export default App
