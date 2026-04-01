import React, { useState, useEffect } from 'react'
import InfoBlock from '../components/InfoBlock.jsx'
import AssetSelector from '../components/AssetSelector.jsx'
import BrainViewer3D from '../components/BrainViewer3D.jsx'
import BrainAnatomyInfo from '../components/BrainAnatomyInfo.jsx'
import ScoreCard from '../components/ScoreCard.jsx'

function TribePage({ campaign, asset }) {
  const [tribeData, setTribeData] = useState(null)
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
      
      // Fetch brain map
      const brainResponse = await fetch(`/api/campaign/${campaign}/brain/${asset}`)
      const brainData = await brainResponse.json()
      
      // Fetch scores
      const scoresResponse = await fetch(`/api/campaign/${campaign}/scores/${asset}`)
      const scoresData = await scoresResponse.json()
      
      setTribeData({
        brain: brainData,
        scores: scoresData
      })
    } catch (err) {
      setError('Failed to load TRIBE data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-32 rounded-lg"></div>
        <div className="skeleton h-96 rounded-lg"></div>
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

  if (!tribeData) {
    return null
  }

  const { brain, scores } = tribeData
  const tribeScores = scores?.tribe || {}

  return (
    <div className="space-y-6">
      {/* Info Block */}
      <InfoBlock
        title="TRIBE — Neural Engagement Scoring"
        description="TRIBE (Temporal Response In Brain Encoding) analysiert Gehirnaktivitätsmuster aus fMRI-Daten. Es misst, wie stark ein Creative die natürliche Aufmerksamkeitsverteilung im Gehirn stimuliert."
        example="Ein hoher neural_engagement Score (z.B. 0.75) bedeutet, dass das Creative die typischen Gehirnaktivierungsmuster für Aufmerksamkeit und Emotion stark aktiviert — ein starkes Signal für Werbewirkung."
      />

      {/* Asset Selector */}
      <AssetSelector
        assets={[asset]}
        selectedAsset={asset}
        onChange={() => {}}
      />

      {/* Brain Anatomy Info */}
      <BrainAnatomyInfo collapsed={false} />

      {/* 3D Brain Viewer */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">TRIBE 3D Brain Map</h3>
        <BrainViewer3D scores={tribeScores} />
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-3 gap-4">
        <ScoreCard
          label="Neural Engagement"
          value={tribeScores.neural_engagement ?? 0}
          tooltip="Wie stark stimuliert das Creative die natürliche Gehirnaktivität?"
        />
        <ScoreCard
          label="Emotional Impact"
          value={tribeScores.emotional_impact ?? 0}
          color="success"
          tooltip="Wie stark werden Emotionen im Gehirn aktiviert?"
        />
        <ScoreCard
          label="Temporal Peak"
          value={tribeScores.temporal_peak ?? 0}
          tooltip="Wie stark ist die zeitliche Aktivierungspike?"
        />
      </div>

      {/* Temporal Profile */}
      {brain.type === 'png' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Temporal Profile</h3>
          <img
            src={brain.path}
            alt="Temporal Profile"
            className="w-full rounded-lg"
          />
        </div>
      )}
    </div>
  )
}

export default TribePage
