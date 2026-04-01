import React, { useState, useEffect, useRef } from 'react'
import InfoBlock from '../components/InfoBlock.jsx'
import AssetSelector from '../components/AssetSelector.jsx'
import ScoreCard from '../components/ScoreCard.jsx'
import * as d3 from 'd3'

function MiroFishPage({ campaign, asset }) {
  const [mirofishData, setMirofishData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState({ status: 'manual', port: 5001 })
  const svgRef = useRef()

  useEffect(() => {
    if (campaign && asset) {
      fetchData()
      checkStatus()
    }
  }, [campaign, asset])

  const checkStatus = async () => {
    try {
      const response = await fetch(`/api/campaign/${campaign}/mirofish/status`)
      const data = await response.json()
      setStatus(data)
    } catch (err) {
      console.error('Failed to check MiroFish status:', err)
    }
  }

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch MiroFish data
      const response = await fetch(`/api/campaign/${campaign}/mirofish/${asset}`)
      const data = await response.json()
      
      setMirofishData(data)
    } catch (err) {
      setError('Failed to load MiroFish data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!mirofishData || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const container = svgRef.current.parentElement
    const width = container?.clientWidth || 800
    const height = 400

    // Demo data if no real data
    const nodes = mirofishData.agents?.length > 0 ? mirofishData.agents :
      Array.from({ length: 60 }, (_, i) => ({
        id: i,
        name: `Agent ${i}`,
        sentiment: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)],
        influence: Math.random(),
        posts: Math.floor(Math.random() * 20)
      }))

    const links = mirofishData.interactions?.length > 0 ? mirofishData.interactions :
      Array.from({ length: 80 }, () => ({
        source: Math.floor(Math.random() * nodes.length),
        target: Math.floor(Math.random() * nodes.length)
      })).filter(l => l.source !== l.target)

    const color = d => ({
      positive: '#059669',
      neutral: '#6b7280',
      negative: '#dc2626'
    })[d.sentiment] || '#6b7280'

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(40))
      .force('charge', d3.forceManyBody().strength(-30))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(8))

    const g = svg.append('g')

    // Zoom
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => g.attr('transform', e.transform)))

    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#1e293b')
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', 1)

    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', d => 4 + (d.influence || 0.5) * 6)
      .attr('fill', color)
      .attr('stroke', '#0f1424')
      .attr('stroke-width', 1.5)
      .call(d3.drag()
        .on('start', (e, d) => {
          if (!e.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (e, d) => {
          d.fx = e.x
          d.fy = e.y
        })
        .on('end', (e, d) => {
          if (!e.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
      )

    // Tooltip
    node.append('title').text(d => `${d.name}\nSentiment: ${d.sentiment}\nPosts: ${d.posts}`)

    simulation.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      node.attr('cx', d => d.x).attr('cy', d => d.y)
    })

    return () => simulation.stop()
  }, [mirofishData])

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

  if (!mirofishData) {
    return null
  }

  const isDemo = mirofishData.demo || mirofishData.agents?.length === 0

  // Calculate sentiment stats
  const agents = mirofishData.agents || []
  const positiveCount = agents.filter(a => a.sentiment === 'positive').length
  const positivePercent = agents.length > 0 ? ((positiveCount / agents.length) * 100).toFixed(1) : 0

  return (
    <div className="space-y-6">
      {/* Info Block */}
      <InfoBlock
        title="MiroFish — Social Simulation"
        description="MiroFish generiert hunderte KI-Agenten mit einzigartigen Persönlichkeiten, die auf einem simulierten Social-Media-Netzwerk auf das Creative reagieren. Das Ergebnis zeigt, wie eine Zielgruppe das Creative wahrnehmen könnte — bevor es live geht."
        example="Eine Simulation mit 200 Agenten zeigt: 68% positive Reaktionen, 15% teilen den Post weiter, aber 12% empfinden den Content als 'zu werblich'. Das gibt frühzeitige Hinweise auf PR-Risiken."
      />

      {/* Status Card */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">MiroFish Status</h3>
            <p className="text-sm text-secondary mt-1">
              {status.status === 'connected'
                ? 'MiroFish Service läuft auf localhost:5001'
                : 'Nutze localhost:3000 für manuelle Simulationen'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`badge ${status.status === 'connected' ? 'badge-success' : 'badge-warning'}`}>
              {status.status === 'connected' ? 'Connected' : 'Manual Mode'}
            </span>
          </div>
        </div>
      </div>

      {/* Agent Network Graph */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Agent Network Graph</h3>
        {isDemo && (
          <div className="mb-4">
            <span className="badge badge-neutral">Demo — keine echten Simulationsdaten</span>
          </div>
        )}
        <svg ref={svgRef} style={{ width: '100%', height: 400, background: 'var(--bg-subtle)', borderRadius: 8 }} />
      </div>

      {/* Sentiment Overview Cards */}
      <div className="grid grid-cols-3 gap-4">
        <ScoreCard
          label="Positive Sentiment"
          value={positivePercent}
          unit="%"
          color="success"
          tooltip="Anteil der Agenten mit positiver Haltung zum Creative"
        />
        <ScoreCard
          label="Virality Score"
          value={mirofishData.virality_score?.toFixed(2) ?? '0.00'}
          tooltip="Wie wahrscheinlich ist Viralität basierend auf Agenten-Interaktionen?"
        />
        <ScoreCard
          label="Controversy Risk"
          value={mirofishData.controversy_risk?.toFixed(2) ?? '0.00'}
          color={mirofishData.controversy_risk > 0.5 ? 'danger' : 'secondary'}
          tooltip="Risiko von negativen Reaktionen und Streit"
        />
      </div>
    </div>
  )
}

export default MiroFishPage
