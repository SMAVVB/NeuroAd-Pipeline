'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'

// MiroFish sentiment data type
export interface MiroFishData {
  positive_sentiment: number
  controversy_risk: number
  virality_score: number
  social_score: number
  [key: string]: number
}

// Agent node for D3 force graph
interface AgentNode {
  id: string
  name: string
  positiveSentiment: number
  controversyRisk: number
  viralityScore: number
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

// Edge for D3 force graph
interface GraphEdge {
  source: AgentNode | string
  target: AgentNode | string
}

// Graph data structure
export interface GraphData {
  nodes: AgentNode[]
  edges: GraphEdge[]
}

// MiroFish graph component props
interface MiroFishGraphProps {
  graphData?: GraphData
  loading?: boolean
  height?: number
}

// Get node color based on sentiment data
function getNodeColor(node: AgentNode): string {
  if (node.positiveSentiment > 0.6) return '#10b981' // green
  if (node.controversyRisk > 0.4) return '#ef4444' // red
  return '#6b7280' // gray
}

// Get node radius based on virality score
function getNodeRadius(viralityScore: number): number {
  // Scale virality (0-1) to radius (8-20)
  return 8 + viralityScore * 12
}

// Generate Agent graph data from MiroFish data
function generateAgentGraphData(creativeName: string, mirofishData: MiroFishData): GraphData {
  const numAgents = 18 // Generate 18 agent nodes

  // Create agent nodes with simulated data based on MiroFish metrics
  const nodes: AgentNode[] = []
  for (let i = 0; i < numAgents; i++) {
    const agentNum = i + 1
    const agentId = `agent-${agentNum.toString().padStart(2, '0')}`

    // Generate agent-specific sentiment values centered around MiroFish scores
    // with some variation to create a realistic network
    const sentimentVariance = (Math.random() - 0.5) * 0.3 // +/- 0.15
    const controversyVariance = (Math.random() - 0.5) * 0.2 // +/- 0.1

    const agentPositiveSentiment = Math.min(1, Math.max(0, mirofishData.positive_sentiment + sentimentVariance))
    const agentControversyRisk = Math.min(1, Math.max(0, mirofishData.controversy_risk + controversyVariance))
    const agentViralityScore = Math.min(1, Math.max(0, mirofishData.virality_score + (Math.random() - 0.5) * 0.2))

    nodes.push({
      id: agentId,
      name: `Agent_${agentNum.toString().padStart(2, '0')}`,
      positiveSentiment: agentPositiveSentiment,
      controversyRisk: agentControversyRisk,
      viralityScore: agentViralityScore,
    })
  }

  // Create edges: connect approximately 30% of nodes randomly
  // Each node connects to 2-4 other nodes on average
  const edges: GraphEdge[] = []
  const edgeSet = new Set<string>()

  nodes.forEach((sourceNode, sourceIndex) => {
    // Each node connects to 2-4 random targets
    const numConnections = 2 + Math.floor(Math.random() * 3)

    for (let i = 0; i < numConnections; i++) {
      const targetIndex = Math.floor(Math.random() * numAgents)
      if (targetIndex !== sourceIndex) {
        const targetNode = nodes[targetIndex]
        const edgeKey = [sourceNode.id, targetNode.id].sort().join('-')

        if (!edgeSet.has(edgeKey)) {
          edgeSet.add(edgeKey)
          edges.push({
            source: sourceNode,
            target: targetNode,
          })
        }
      }
    }
  })

  return { nodes, edges }
}

// Popup component for node details
function NodePopup({ node, onClose }: { node: AgentNode; onClose: () => void }) {
  return (
    <div className="absolute z-50 bg-white border border-gray-200 rounded-lg shadow-xl p-4 w-64">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">{node.name}</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          ×
        </button>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between p-2 bg-green-50 rounded border border-green-100">
          <span className="text-gray-600">Positive Sentiment</span>
          <span className="font-mono font-semibold text-green-700">
            {(node.positiveSentiment * 100).toFixed(0)}%
          </span>
        </div>

        <div className="flex items-center justify-between p-2 bg-red-50 rounded border border-red-100">
          <span className="text-gray-600">Controversy Risk</span>
          <span className="font-mono font-semibold text-red-700">
            {(node.controversyRisk * 100).toFixed(0)}%
          </span>
        </div>

        <div className="flex items-center justify-between p-2 bg-amber-50 rounded border border-amber-100">
          <span className="text-gray-600">Virality Score</span>
          <span className="font-mono font-semibold text-amber-700">
            {(node.viralityScore * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  )
}

// Main Graph component
export default function MiroFishGraph({
  graphData,
  loading = false,
  height = 600,
}: MiroFishGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<AgentNode | null>(null)
  const [popupPosition, setPopupPosition] = useState<{ x: number; y: number } | null>(null)

  // Render graph using D3
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !graphData) return

    const svg = d3.select(svgRef.current)
    const container = containerRef.current
    const width = container.clientWidth
    const heightVal = height

    // Clear previous SVG content
    svg.selectAll('*').remove()

    const nodesData = graphData.nodes || []
    const edgesData = graphData.edges || []

    if (nodesData.length === 0) return

    // Create simulation
    const simulation = d3.forceSimulation(nodesData as AgentNode[])
      .force('link', d3.forceLink(edgesData as GraphEdge[]).id((d) => (d as AgentNode).id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, heightVal / 2))
      .force('collide', d3.forceCollide((d) => getNodeRadius(d.viralityScore) + 5))

    // Create SVG groups
    const g = svg.append('g')

    // Zoom
    const zoomed = (event: d3.D3ZoomEvent<SVGSVGElement, any>) => {
      g.attr('transform', event.transform as any)
    }

    const zoomBehavior = d3
      .zoom<SVGSVGElement, any>()
      .extent([[0, 0], [width, heightVal]])
      .scaleExtent([0.1, 4])
      .on('zoom', zoomed)

    svg.call(zoomBehavior)
      .on('click', () => {
        setSelectedNode(null)
        setPopupPosition(null)
      })

    // Links group
    const linkGroup = g.append('g').attr('class', 'links')

    // Render links
    const links = linkGroup
      .selectAll<SVGPathElement, GraphEdge>('path')
      .data(edgesData)
      .enter()
      .append('path')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 1.5)
      .attr('fill', 'none')
      .attr('opacity', 0.6)

    // Nodes group
    const nodeGroup = g.append('g').attr('class', 'nodes')

    // Render nodes
    const nodes = nodeGroup
      .selectAll<SVGCircleElement, AgentNode>('circle')
      .data(nodesData)
      .enter()
      .append('circle')
      .attr('r', (d) => getNodeRadius(d.viralityScore))
      .attr('fill', getNodeColor)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .style('pointer-events', 'all')
      .on('click', (event, d) => {
        event.stopPropagation()

        const rect = (event.currentTarget as SVGCircleElement).getBoundingClientRect()
        const svgRect = svgRef.current?.getBoundingClientRect()
        if (svgRect) {
          setPopupPosition({
            x: rect.left - svgRect.left + 20,
            y: rect.top - svgRect.top + 20,
          })
        }

        setSelectedNode(d)
      })
      .on('mouseenter', (event) => {
        d3.select(event.currentTarget).attr('stroke', '#3b82f6').attr('stroke-width', 3)
      })
      .on('mouseleave', (event) => {
        if (!selectedNode) return
        // Get the bound data from the selection context
        const nodeDatum = nodesData.find(n => n.id === selectedNode.id)
        if (nodeDatum && selectedNode.id !== nodeDatum.id) {
          d3.select(event.currentTarget).attr('stroke', '#fff').attr('stroke-width', 2)
        }
      })

    // Node labels
    const labels = nodeGroup
      .selectAll<SVGTextElement, AgentNode>('text')
      .data(nodesData)
      .enter()
      .append('text')
      .text((d) => d.name)
      .attr('font-size', '10px')
      .attr('fill', '#475569')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => getNodeRadius(d.viralityScore) + 12)
      .attr('font-weight', '500')
      .style('pointer-events', 'none')
      .style('font-family', 'Inter, system-ui, sans-serif')

    // Simulation tick handler
    simulation.on('tick', () => {
      // Update link paths
      links.attr('d', (d) => {
        const source = d.source as AgentNode
        const target = d.target as AgentNode
        return `M${source.x || 0},${source.y || 0} L${target.x || 0},${target.y || 0}`
      })

      // Update node positions
      nodes.attr('cx', (d) => d.x || 0).attr('cy', (d) => d.y || 0)

      // Update node labels
      labels.attr('x', (d) => d.x || 0).attr('y', (d) => d.y || 0)
    })

    // Drag behavior
    function dragstarted(event: any, d: AgentNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: any, d: AgentNode) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: any, d: AgentNode) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    const dragBehavior = d3.drag<SVGCircleElement, AgentNode>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended)

    nodes.call(dragBehavior as any)

    // Handle window resize
    const handleResize = () => {
      const newWidth = container.clientWidth
      const newHeight = heightVal
      svg.attr('width', newWidth).attr('height', newHeight)
      simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2)).alpha(0.1).restart()
    }

    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(container)

    // Cleanup
    return () => {
      resizeObserver.disconnect()
      simulation.stop()
    }
  }, [graphData, height, selectedNode])

  // Close popup
  const closePopup = useCallback(() => {
    setSelectedNode(null)
    setPopupPosition(null)
  }, [])

  return (
    <div className="flex flex-col h-full w-full">
      {/* Graph container */}
      <div
        ref={containerRef}
        className="flex-1 relative bg-[#FAFAFA] bg-[radial-gradient(#D0D0D0_1.5px,transparent_1.5px)] bg-[length:24px_24px]"
        style={{ minHeight: height }}
      >
        <svg ref={svgRef} className="w-full h-full block" />

        {/* Loading state */}
        {loading && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
            <div className="w-10 h-10 border-3 border-gray-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-gray-500">Loading graph data...</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !graphData && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
            <div className="text-48px opacity-20 mb-3">❖</div>
            <p className="text-gray-500">Waiting for graph data...</p>
          </div>
        )}

        {/* Legend - Bottom Left */}
        {graphData && (
          <div className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-sm px-4 py-3 rounded-lg border border-gray-100 shadow-sm z-10">
            <span className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">
              Legend
            </span>
            <div className="flex flex-wrap gap-4 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#10b981]" />
                <span className="text-gray-600">High Positive Sentiment</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#ef4444]" />
                <span className="text-gray-600">Controversy Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#6b7280]" />
                <span className="text-gray-600">Neutral</span>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-2 text-xs text-gray-500">
              <span className="w-2 h-2 rounded-full bg-gray-400" />
              <span>Node size ∝ Virality Score</span>
            </div>
          </div>
        )}
      </div>

      {/* Node Popup */}
      {selectedNode && popupPosition && (
        <NodePopup
          node={selectedNode}
          onClose={closePopup}
        />
      )}
    </div>
  )
}
