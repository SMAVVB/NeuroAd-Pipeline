import React, { useState, useEffect } from 'react'
import InfoBlock from '../components/InfoBlock.jsx'
import AssetSelector from '../components/AssetSelector.jsx'
import ScoreCard from '../components/ScoreCard.jsx'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function ClipPage({ campaign, asset }) {
  const [clipData, setClipData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (campaign && asset) {
      fetchData()
    }
  }, [campaign, asset])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch CLIP scores
      const response = await fetch(`/api/campaign/${campaign}/clip/${asset}`)
      const data = await response.json()
      
      setClipData(data)
    } catch (err) {
      setError('Failed to load CLIP data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-32 rounded-lg"></div>
        <div className="skeleton h-64 rounded-lg"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-8 text-center">
        <p className="text-danger">{error}</p>
      </div>
    )
  }

  if (!clipData) {
    return null
  }

  const { brand_match_score, top_label, label_scores = [] } = clipData

  // Prepare bar chart data
  const chartData = label_scores.map(item => ({
    name: item.label || 'Label',
    score: item.score ?? 0,
  }))

  return (
    <div className="space-y-6">
      {/* Info Block */}
      <InfoBlock
        title="CLIP — Brand Consistency Scoring"
        description="CLIP (Contrastive Language-Image Pre-Training) misst die semantische Ähnlichkeit zwischen einem Bild und Text-Beschreibungen. Wir nutzen es um zu prüfen, ob ein Creative zur definierten Marken-Positionierung passt."
        example="Labels wie 'sleek minimalist design' oder 'vibrant colorful energy' werden gegen die Frames des Videos verglichen. Ein Score von 0.4 bedeutet 40% Übereinstimmung mit dem Label."
      />

      {/* Asset Selector */}
      <AssetSelector
        assets={[asset]}
        selectedAsset={asset}
        onChange={() => {}}
      />

      {/* Brand Match Score */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Brand Match Score</h3>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-secondary mb-1">Top Label</div>
            <div className="text-2xl font-bold">{top_label || 'N/A'}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-secondary mb-1">Match Score</div>
            <div className="text-5xl font-bold text-accent">
              {brand_match_score?.toFixed(2) ?? '0.00'}
            </div>
          </div>
        </div>
      </div>

      {/* All Label Scores */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">All Label Scores</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 20, right: 30, left: 40, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" domain={[0, 1]} stroke="#8b9bb4" />
            <YAxis dataKey="name" type="category" width={150} stroke="#8b9bb4" />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f1424', border: '1px solid #1e293b', color: '#ffffff' }}
            />
            <Legend />
            <Bar dataKey="score" fill="#00d4ff" barSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ClipPage
