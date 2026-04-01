import React, { useState, useEffect } from 'react'
import InfoBlock from '../components/InfoBlock.jsx'
import AssetSelector from '../components/AssetSelector.jsx'
import ScoreCard from '../components/ScoreCard.jsx'
import { RadialBarChart, RadialBar, Legend, ResponsiveContainer } from 'recharts'

function EmotionPage({ campaign, asset }) {
  const [emotionData, setEmotionData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasFaces, setHasFaces] = useState(true)

  useEffect(() => {
    if (campaign && asset) {
      fetchData()
    }
  }, [campaign, asset])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch emotion scores
      const response = await fetch(`/api/campaign/${campaign}/emotion/${asset}`)
      const data = await response.json()
      
      setEmotionData(data)
      setHasFaces(!!data.dominant_emotion || data.emotional_valence !== undefined)
    } catch (err) {
      setError('Failed to load emotion data')
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

  if (!emotionData) {
    return null
  }

  const { dominant_emotion, emotional_valence, face_coverage = 0, emotion_distribution = [] } = emotionData

  // Prepare radial bar chart data
  const chartData = [
    { name: 'Valence', value: (emotional_valence + 1) * 50, fill: emotional_valence >= 0 ? '#059669' : '#dc2626' },
  ]

  if (!hasFaces) {
    return (
      <div className="space-y-6">
        <InfoBlock
          title="HSEmotion — Facial Emotion Recognition"
          description="HSEmotion erkennt Emotionen in menschlichen Gesichtern in jedem Frame des Videos. Das Modell wurde auf AffectNet trainiert und gibt sowohl diskrete Emotionen (Freude, Trauer, etc.) als auch kontinuierliche Valenz-Werte aus."
          example="Ein Creative mit vielen Frames hoher Freude (happiness) und positiver Valenz signalisiert, dass die dargestellten Personen authentisch positiv wirken — ein starkes Signal für Werbewirkung."
        />
        <div className="card p-8 text-center">
          <div className="text-4xl mb-4">😐</div>
          <h3 className="text-lg font-semibold mb-2">Keine Gesichter erkannt</h3>
          <p className="text-secondary">
            HSEmotion ist nur relevant für Werbung mit echten Menschen.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Info Block */}
      <InfoBlock
        title="HSEmotion — Facial Emotion Recognition"
        description="HSEmotion erkennt Emotionen in menschlichen Gesichtern in jedem Frame des Videos. Das Modell wurde auf AffectNet trainiert und gibt sowohl diskrete Emotionen (Freude, Trauer, etc.) als auch kontinuierliche Valenz-Werte aus."
        example="Ein Creative mit vielen Frames hoher Freude (happiness) und positiver Valenz signalisiert, dass die dargestellten Personen authentisch positiv wirken — ein starkes Signal für Werbewirkung."
      />

      {/* Asset Selector */}
      <AssetSelector
        assets={[asset]}
        selectedAsset={asset}
        onChange={() => {}}
      />

      {/* Emotion Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <div className="text-sm font-semibold text-secondary mb-2">Dominant Emotion</div>
          <div className="text-3xl font-bold text-accent">
            {dominant_emotion ? (
              <span className="badge badge-success">{dominant_emotion}</span>
            ) : (
              <span className="text-secondary">N/A</span>
            )}
          </div>
        </div>

        <div className="card">
          <div className="text-sm font-semibold text-secondary mb-2">Emotional Valence</div>
          <div className={`text-3xl font-bold ${emotional_valence >= 0 ? 'text-success' : 'text-danger'}`}>
            {emotional_valence?.toFixed(2) ?? '0.00'}
          </div>
          <div className="text-xs text-secondary mt-1">
            {emotional_valence >= 0 ? 'Positiv' : 'Negativ'}
          </div>
        </div>

        <ScoreCard
          label="Face Coverage"
          value={face_coverage.toFixed(1)}
          unit="%"
          tooltip="Prozentsatz der Frames mit erkannten Gesichtern"
        />
      </div>

      {/* Valence Gauge */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Emotional Valence Gauge</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="100%"
            barSize={10}
            data={chartData}
            startAngle={180}
            endAngle={0}
          >
            <RadialBar
              minAngle={15}
              label={{ fill: '#8b9bb4', position: 'insideStart' }}
              background={{ fill: '#1e293b' }}
              dataKey="value"
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-8 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-success"></div>
            <span className="text-sm text-secondary">Positiv (+1)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-danger"></div>
            <span className="text-sm text-secondary">Negativ (-1)</span>
          </div>
        </div>
      </div>

      {/* Emotion Distribution */}
      {emotion_distribution.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Emotion Distribution</h3>
          <div className="grid grid-cols-3 gap-4">
            {emotion_distribution.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium">{item.emotion || 'Emotion'}</span>
                <span className="text-sm font-bold text-accent">{(item.score * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EmotionPage
