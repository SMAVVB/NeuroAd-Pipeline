import React, { useState, useEffect } from 'react'
import InfoBlock from '../components/InfoBlock.jsx'
import AssetSelector from '../components/AssetSelector.jsx'
import ScoreCard from '../components/ScoreCard.jsx'

function SaliencyPage({ campaign, asset }) {
  const [saliencyData, setSaliencyData] = useState(null)
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
      
      // Fetch saliency frames
      const framesResponse = await fetch(`/api/campaign/${campaign}/saliency/${asset}`)
      const framesData = await framesResponse.json()
      
      // Fetch scores
      const scoresResponse = await fetch(`/api/campaign/${campaign}/scores/${asset}`)
      const scoresData = await scoresResponse.json()
      
      setSaliencyData({
        frames: framesData.frames || [],
        heatmap: framesData.heatmap,
        scores: scoresData
      })
    } catch (err) {
      setError('Failed to load saliency data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-32 rounded-lg"></div>
        <div className="grid grid-cols-3 gap-4">
          <div className="skeleton h-48 rounded-lg"></div>
          <div className="skeleton h-48 rounded-lg"></div>
          <div className="skeleton h-48 rounded-lg"></div>
        </div>
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

  if (!saliencyData) {
    return null
  }

  const { frames, heatmap, scores } = saliencyData

  // Extract scores
  const centerBias = scores?.saliency?.center_bias ?? 0
  const meanSaliency = scores?.saliency?.saliency_score ?? 0
  const temporalVariance = scores?.saliency?.temporal_variance ?? 0

  return (
    <div className="space-y-6">
      {/* Info Block */}
      <InfoBlock
        title="ViNet-S — Visual Attention Prediction"
        description="ViNet-S simuliert Eye-Tracking — es sagt vorher, wohin ein Mensch zuerst schaut. Das Modell wurde auf DHF1K trainiert, einem Datensatz mit echten Eye-Tracking-Aufnahmen von Videos."
        example="Ein hoher Center Bias bedeutet, dass die Aufmerksamkeit im Bildmittelpunkt konzentriert ist — typisch für professionelle Produktshots. Bei niedrigem Center Bias wandert der Blick mehr über das Bild."
      />

      {/* Asset Selector */}
      <AssetSelector
        assets={[asset]}
        selectedAsset={asset}
        onChange={() => {}}
      />

      {/* Score Cards */}
      <div className="grid grid-cols-3 gap-4">
        <ScoreCard
          label="Center Bias"
          value={centerBias.toFixed(3)}
          tooltip="Anteil der Aufmerksamkeit im zentralen 50% des Bildes. 1.0 = alles im Zentrum, 0.5 = gleichmäßig verteilt."
        />
        <ScoreCard
          label="Mean Saliency"
          value={meanSaliency.toFixed(3)}
          tooltip="Durchschnittliche Salienz-Intensität. Höhere Werte = insgesamt stärkere visuelle Reize."
        />
        <ScoreCard
          label="Temporal Variance"
          value={temporalVariance.toFixed(3)}
          tooltip="Wie stark verschiebt sich die Aufmerksamkeit von Frame zu Frame. Hohe Varianz = dynamische, wechselnde Aufmerksamkeitspunkte."
        />
      </div>

      {/* Saliency Frames Grid */}
      {frames.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Saliency Frames</h3>
          <div className="grid grid-cols-4 gap-4">
            {frames.map((frame) => (
              <div key={frame.frame} className="relative group">
                <img
                  src={frame.path}
                  alt={`Frame ${frame.frame}`}
                  className="w-full h-48 object-cover rounded-lg"
                />
                <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  Frame {frame.frame}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Heatmap */}
      {heatmap && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Saliency Heatmap</h3>
          <img
            src={heatmap}
            alt="Saliency Heatmap"
            className="w-full rounded-lg"
          />
        </div>
      )}
    </div>
  )
}

export default SaliencyPage
