'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'

// Types for MiroFish graph data
export interface Entity {
  uuid: string
  name: string
  labels: string[]
  attributes?: Record<string, string | number | boolean>
  summary?: string
  created_at?: string
  updated_at?: string
}

export interface EntityEdge {
  uuid: string
  source_node_uuid: string
  target_node_uuid: string
  name?: string
  fact_type?: string
  fact?: string
  episodes?: string[]
  created_at?: string
  valid_at?: string
}

export interface GraphData {
  nodes: Entity[]
  edges: EntityEdge[]
}

// Entity type color mapping
const ENTITY_COLOR_MAP: Record<string, string> = {
  Person: '#FF6B35',
  Company: '#004E89',
  MediaOutlet: '#7B2D8E',
  Product: '#1A936F',
  Location: '#C5283D',
  Event: '#E9724C',
  Topic: '#3498db',
  Concept: '#9b59b6',
  Other: '#27ae60',
}

// Get color for entity type
function getEntityTypeColor(type: string): string {
  return ENTITY_COLOR_MAP[type] || ENTITY_COLOR_MAP['Other']
}

// Format datetime
function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
  } catch {
    return dateStr
  }
}

// Node data structure for D3
interface NodeData {
  id: string
  name: string
  type: string
  rawData: Entity
  x?: number
  y?: number
  fx?: number
  fy?: number
}

// Edge data structure for D3
interface EdgeData {
  source: string
  target: string
  type: string
  name: string
  curvature: number
  isSelfLoop: boolean
  pairIndex?: number
  pairTotal?: number
  rawData: EntityEdge | SelfLoopGroup
}

// Self-loop group for aggregating multiple edges between same nodes
interface SelfLoopGroup {
  isSelfLoopGroup: boolean
  source_name: string
  target_name: string
  selfLoopCount: number
  selfLoopEdges: EntityEdge[]
}

interface SelectedItem {
  type: 'node' | 'edge'
  data: Entity | EntityEdge | SelfLoopGroup
  entityType?: string
  color?: string
}

// Graph component props
interface MiroFishGraphProps {
  graphData?: GraphData
  loading?: boolean
  height?: number
}

// Main Graph component
export default function MiroFishGraph({
  graphData,
  loading = false,
  height = 600,
}: MiroFishGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null)
  const [showEdgeLabels, setShowEdgeLabels] = useState(true)
  const [expandedSelfLoops, setExpandedSelfLoops] = useState<Set<string>>(new Set())
  const [entityTypes, setEntityTypes] = useState<Array<{ name: string; count: number; color: string }>>([])

  // Calculate entity types for legend
  useEffect(() => {
    if (!graphData?.nodes) {
      setEntityTypes([])
      return
    }

    const typeMap: Record<string, { name: string; count: number; color: string }> = {}
    const colors = [
      '#FF6B35', '#004E89', '#7B2D8E', '#1A936F', '#C5283D',
      '#E9724C', '#3498db', '#9b59b6', '#27ae60', '#f39c12',
    ]

    graphData.nodes.forEach((node) => {
      const type = node.labels.find((l) => l !== 'Entity') || 'Entity'
      if (!typeMap[type]) {
        typeMap[type] = {
          name: type,
          count: 0,
          color: colors[Object.keys(typeMap).length % colors.length],
        }
      }
      typeMap[type].count++
    })

    setEntityTypes(Object.values(typeMap))
  }, [graphData?.nodes])

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

    // Prepare node data
    const nodes: NodeData[] = nodesData.map((n) => ({
      id: n.uuid,
      name: n.name || 'Unnamed',
      type: n.labels.find((l) => l !== 'Entity') || 'Entity',
      rawData: n,
    }))

    const nodeMap: Record<string, Entity> = {}
    nodesData.forEach((n) => {
      nodeMap[n.uuid] = n
    })

    const nodeIds = new Set(nodes.map((n) => n.id))

    // Process edge data
    const edgePairCount: Record<string, number> = {}
    const selfLoopEdges: Record<string, EntityEdge[]> = {}
    const tempEdges = edgesData.filter(
      (e) => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid)
    )

    // Count edges and collect self-loops
    tempEdges.forEach((e) => {
      if (e.source_node_uuid === e.target_node_uuid) {
        if (!selfLoopEdges[e.source_node_uuid]) {
          selfLoopEdges[e.source_node_uuid] = []
        }
        selfLoopEdges[e.source_node_uuid].push({
          ...e,
          source_name: nodeMap[e.source_node_uuid]?.name,
          target_name: nodeMap[e.target_node_uuid]?.name,
        })
      } else {
        const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
        edgePairCount[pairKey] = (edgePairCount[pairKey] || 0) + 1
      }
    })

    // Create edges array
    const edgePairIndex: Record<string, number> = {}
    const processedSelfLoopNodes = new Set<string>()
    const edges: EdgeData[] = []

    tempEdges.forEach((e) => {
      const isSelfLoop = e.source_node_uuid === e.target_node_uuid

      if (isSelfLoop) {
        if (processedSelfLoopNodes.has(e.source_node_uuid)) {
          return
        }
        processedSelfLoopNodes.add(e.source_node_uuid)

        const allSelfLoops = selfLoopEdges[e.source_node_uuid] || []
        const nodeName = nodeMap[e.source_node_uuid]?.name || 'Unknown'

        edges.push({
          source: e.source_node_uuid,
          target: e.target_node_uuid,
          type: 'SELF_LOOP',
          name: `Self Relations (${allSelfLoops.length})`,
          curvature: 0,
          isSelfLoop: true,
          rawData: {
            isSelfLoopGroup: true,
            source_name: nodeName,
            target_name: nodeName,
            selfLoopCount: allSelfLoops.length,
            selfLoopEdges: allSelfLoops,
          },
        })
        return
      }

      const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
      const totalCount = edgePairCount[pairKey]
      const currentIndex = edgePairIndex[pairKey] || 0
      edgePairIndex[pairKey] = currentIndex + 1

      const isReversed = e.source_node_uuid > e.target_node_uuid

      // Calculate curvature
      let curvature = 0
      if (totalCount > 1) {
        const curvatureRange = Math.min(1.2, 0.6 + totalCount * 0.15)
        curvature = ((currentIndex / (totalCount - 1)) - 0.5) * curvatureRange * 2
        if (isReversed) {
          curvature = -curvature
        }
      }

      edges.push({
        source: e.source_node_uuid,
        target: e.target_node_uuid,
        type: e.fact_type || e.name || 'RELATED',
        name: e.name || e.fact_type || 'RELATED',
        curvature,
        isSelfLoop: false,
        pairIndex: currentIndex,
        pairTotal: totalCount,
        rawData: {
          ...e,
          source_name: nodeMap[e.source_node_uuid]?.name,
          target_name: nodeMap[e.target_node_uuid]?.name,
        },
      })
    })

    // Color scale
    const colorMap: Record<string, string> = {}
    entityTypes.forEach((t) => {
      colorMap[t.name] = t.color
    })
    const getColor = (type: string) => colorMap[type] || '#999'

    // Create simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        'link',
        d3
          .forceLink(edges)
          .id((d) => d.id)
          .distance((d) => {
            const baseDistance = 150
            const edgeCount = d.pairTotal || 1
            return baseDistance + (edgeCount - 1) * 50
          })
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, heightVal / 2))
      .force('collide', d3.forceCollide(50))
      .force('x', d3.forceX(width / 2).strength(0.04))
      .force('y', d3.forceY(heightVal / 2).strength(0.04))

    // Create SVG groups
    const g = svg.append('g')

    // Zoom
    svg
      .call(
        d3
          .zoom()
          .extent([[0, 0], [width, heightVal]])
          .scaleExtent([0.1, 4])
          .on('zoom', (event) => {
            g.attr('transform', event.transform)
          })
      )
      .on('click', () => {
        setSelectedItem(null)
      })

    // Links group
    const linkGroup = g.append('g').attr('class', 'links')

    // Calculate link path
    const getLinkPath = (d: EdgeData): string => {
      const sx = (d.source as NodeData).x || 0
      const sy = (d.source as NodeData).y || 0
      const tx = (d.target as NodeData).x || 0
      const ty = (d.target as NodeData).y || 0

      if (d.isSelfLoop) {
        const loopRadius = 30
        const x1 = sx + 8
        const y1 = sy - 4
        const x2 = sx + 8
        const y2 = sy + 4
        return `M${x1},${y1} A${loopRadius},${loopRadius} 0 1,1 ${x2},${y2}`
      }

      if (d.curvature === 0) {
        return `M${sx},${sy} L${tx},${ty}`
      }

      const dx = tx - sx
      const dy = ty - sy
      const dist = Math.sqrt(dx * dx + dy * dy)
      const pairTotal = d.pairTotal || 1
      const offsetRatio = 0.25 + pairTotal * 0.05
      const baseOffset = Math.max(35, dist * offsetRatio)
      const offsetX = -dy / dist / dist * d.curvature * baseOffset
      const offsetY = dx / dist / dist * d.curvature * baseOffset
      const cx = (sx + tx) / 2 + offsetX
      const cy = (sy + ty) / 2 + offsetY

      return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`
    }

    // Calculate link midpoint
    const getLinkMidpoint = (d: EdgeData): { x: number; y: number } => {
      const sx = (d.source as NodeData).x || 0
      const sy = (d.source as NodeData).y || 0
      const tx = (d.target as NodeData).x || 0
      const ty = (d.target as NodeData).y || 0

      if (d.isSelfLoop) {
        return { x: sx + 70, y: sy }
      }

      if (d.curvature === 0) {
        return { x: (sx + tx) / 2, y: (sy + ty) / 2 }
      }

      const dx = tx - sx
      const dy = ty - sy
      const dist = Math.sqrt(dx * dx + dy * dy)
      const pairTotal = d.pairTotal || 1
      const offsetRatio = 0.25 + pairTotal * 0.05
      const baseOffset = Math.max(35, dist * offsetRatio)
      const offsetX = -dy / dist / dist * d.curvature * baseOffset
      const offsetY = dx / dist / dist * d.curvature * baseOffset
      const cx = (sx + tx) / 2 + offsetX
      const cy = (sy + ty) / 2 + offsetY

      const midX = 0.25 * sx + 0.5 * cx + 0.25 * tx
      const midY = 0.25 * sy + 0.5 * cy + 0.25 * ty

      return { x: midX, y: midY }
    }

    // Render links
    const link = linkGroup
      .selectAll('path')
      .data(edges)
      .enter()
      .append('path')
      .attr('stroke', '#C0C0C0')
      .attr('stroke-width', 1.5)
      .attr('fill', 'none')
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
        linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
        linkLabels.attr('fill', '#666')
        d3.select(event.target).attr('stroke', '#3498db').attr('stroke-width', 3)

        setSelectedItem({
          type: 'edge',
          data: d.rawData,
        })
      })

    // Link labels background
    const linkLabelBg = linkGroup
      .selectAll('rect')
      .data(edges)
      .enter()
      .append('rect')
      .attr('fill', 'rgba(255,255,255,0.95)')
      .attr('rx', 3)
      .attr('ry', 3)
      .style('cursor', 'pointer')
      .style('pointer-events', 'all')
      .style('display', showEdgeLabels ? 'block' : 'none')
      .on('click', (event, d) => {
        event.stopPropagation()
        linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
        linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
        linkLabels.attr('fill', '#666')
        link.filter((l) => l === d).attr('stroke', '#3498db').attr('stroke-width', 3)
        d3.select(event.target).attr('fill', 'rgba(52, 152, 219, 0.1)')

        setSelectedItem({
          type: 'edge',
          data: d.rawData,
        })
      })

    // Link labels
    const linkLabels = linkGroup
      .selectAll('text')
      .data(edges)
      .enter()
      .append('text')
      .text((d) => d.name)
      .attr('font-size', '9px')
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .style('cursor', 'pointer')
      .style('pointer-events', 'all')
      .style('font-family', 'system-ui, sans-serif')
      .style('display', showEdgeLabels ? 'block' : 'none')
      .on('click', (event, d) => {
        event.stopPropagation()
        linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
        linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
        linkLabels.attr('fill', '#666')
        link.filter((l) => l === d).attr('stroke', '#3498db').attr('stroke-width', 3)
        d3.select(event.target).attr('fill', '#3498db')

        setSelectedItem({
          type: 'edge',
          data: d.rawData,
        })
      })

    // Nodes group
    const nodeGroup = g.append('g').attr('class', 'nodes')

    // Node circles
    const node = nodeGroup
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', 10)
      .attr('fill', (d) => getColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2.5)
      .style('cursor', 'pointer')
      .call(
        d3
          .drag()
          .on('start', (event, d) => {
            d.fx = d.x
            d.fy = d.y
            d._dragStartX = event.x
            d._dragStartY = event.y
            d._isDragging = false
          })
          .on('drag', (event, d) => {
            const dx = event.x - (d._dragStartX || 0)
            const dy = event.y - (d._dragStartY || 0)
            const distance = Math.sqrt(dx * dx + dy * dy)

            if (!d._isDragging && distance > 3) {
              d._isDragging = true
              simulation.alphaTarget(0.3).restart()
            }

            if (d._isDragging) {
              d.fx = event.x
              d.fy = event.y
            }
          })
          .on('end', (event, d) => {
            if (d._isDragging) {
              simulation.alphaTarget(0)
            }
            d.fx = null
            d.fy = null
            d._isDragging = false
          })
      )
      .on('click', (event, d) => {
        event.stopPropagation()
        node.attr('stroke', '#fff').attr('stroke-width', 2.5)
        linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
        d3.select(event.target).attr('stroke', '#E91E63').attr('stroke-width', 4)
        link.filter((l) => (l.source as NodeData).id === d.id || (l.target as NodeData).id === d.id)
          .attr('stroke', '#E91E63')
          .attr('stroke-width', 2.5)

        setSelectedItem({
          type: 'node',
          data: d.rawData,
          entityType: d.type,
          color: getColor(d.type),
        })
      })
      .on('mouseenter', (event, d) => {
        if (!selectedItem || (selectedItem.type === 'node' && selectedItem.data.uuid !== d.rawData.uuid)) {
          d3.select(event.target).attr('stroke', '#333').attr('stroke-width', 3)
        }
      })
      .on('mouseleave', (event, d) => {
        if (!selectedItem || (selectedItem.type === 'node' && selectedItem.data.uuid !== d.rawData.uuid)) {
          d3.select(event.target).attr('stroke', '#fff').attr('stroke-width', 2.5)
        }
      })

    // Node labels
    const nodeLabels = nodeGroup
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text((d) => (d.name.length > 12 ? d.name.substring(0, 12) + '...' : d.name))
      .attr('font-size', '11px')
      .attr('fill', '#333')
      .attr('font-weight', '500')
      .attr('dx', 14)
      .attr('dy', 4)
      .style('pointer-events', 'none')
      .style('font-family', 'Inter, system-ui, sans-serif')

    // Simulation tick handler
    simulation.on('tick', () => {
      // Update link paths
      link.attr('d', (d) => getLinkPath(d))

      // Update edge label positions
      linkLabels.each(function (d) {
        const mid = getLinkMidpoint(d)
        d3.select(this).attr('x', mid.x).attr('y', mid.y).attr('transform', '')
      })

      // Update edge label background
      linkLabelBg.each(function (d, i) {
        const mid = getLinkMidpoint(d)
        const textEl = linkLabels.nodes()[i]
        const bbox = textEl?.getBBox()
        if (bbox) {
          d3.select(this)
            .attr('x', mid.x - bbox.width / 2 - 4)
            .attr('y', mid.y - bbox.height / 2 - 2)
            .attr('width', bbox.width + 8)
            .attr('height', bbox.height + 4)
            .attr('transform', '')
        }
      })

      // Update node positions
      node.attr('cx', (d) => d.x || 0).attr('cy', (d) => d.y || 0)

      // Update node labels
      nodeLabels.attr('x', (d) => d.x || 0).attr('y', (d) => d.y || 0)
    })

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
  }, [graphData, height, entityTypes, selectedItem, showEdgeLabels, expandedSelfLoops])

  // Toggle self-loop expand state
  const toggleSelfLoop = useCallback((id: string) => {
    setExpandedSelfLoops((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }, [])

  // Get entity type from labels
  const getEntityType = (labels: string[]): string => {
    return labels.find((l) => l !== 'Entity') || 'Entity'
  }

  // Close detail panel
  const closeDetailPanel = useCallback(() => {
    setSelectedItem(null)
    setExpandedSelfLoops(new Set())
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
            <p className="text-gray-500">Waiting for ontology generation...</p>
          </div>
        )}

        {/* Legend - Bottom Left */}
        {graphData && entityTypes.length > 0 && (
          <div className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-sm px-4 py-3 rounded-lg border border-gray-100 shadow-sm z-10">
            <span className="block text-xs font-semibold text-indigo-600 mb-2 uppercase tracking-wider">
              Entity Types
            </span>
            <div className="flex flex-wrap gap-3 max-w-[320px]">
              {entityTypes.map((type) => (
                <div key={type.name} className="flex items-center gap-2 text-xs text-gray-600">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: type.color }}
                  />
                  <span>{type.name}</span>
                  <span className="text-gray-400 text-[10px]">({type.count})</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Edge Labels Toggle - Top Right */}
        {graphData && (
          <div className="absolute top-6 right-6 flex items-center gap-2 bg-white px-3.5 py-2 rounded-full border border-gray-200 shadow-sm z-10">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only"
                checked={showEdgeLabels}
                onChange={() => setShowEdgeLabels(!showEdgeLabels)}
              />
              <div className="w-10 h-6 bg-gray-200 rounded-full peer peer-checked:indigo-600 transition-colors" />
              <div className="absolute left-1 w-4 h-4 bg-white rounded-full shadow peer-checked:translate-x-4 transition-transform" />
            </label>
            <span className="text-xs text-gray-600">Show Edge Labels</span>
          </div>
        )}

        {/* Detail Panel - Right Side */}
        {selectedItem && (
          <div className="absolute top-6 right-6 w-80 max-h-[calc(100%-48px)] bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden z-20 flex flex-col">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-gray-50">
              <span className="font-semibold text-gray-900">
                {selectedItem.type === 'node' ? 'Node Details' : 'Relationship'}
              </span>
              {selectedItem.type === 'node' && selectedItem.entityType && (
                <span
                  className="px-2.5 py-1 rounded-full text-[10px] font-medium text-white"
                  style={{ backgroundColor: selectedItem.color }}
                >
                  {selectedItem.entityType}
                </span>
              )}
              <button
                onClick={closeDetailPanel}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ×
              </button>
            </div>

            <div className="p-4 overflow-y-auto max-h-[calc(100vh-200px)]">
              {selectedItem.type === 'node' ? (
                // Node Details
                <NodeDetails entity={selectedItem.data as Entity} />
              ) : (
                // Edge Details
                <EdgeDetails
                  edge={selectedItem.data as EntityEdge | SelfLoopGroup}
                  toggleSelfLoop={toggleSelfLoop}
                  expandedSelfLoops={expandedSelfLoops}
                  closeDetailPanel={closeDetailPanel}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Node details component
function NodeDetails({ entity }: { entity: Entity }) {
  return (
    <div className="space-y-4">
      {/* Name */}
      <div className="pb-3 border-b border-gray-100">
        <p className="text-lg font-semibold text-gray-900">{entity.name}</p>
        <p className="text-xs text-gray-500 font-mono mt-1">{entity.uuid}</p>
      </div>

      {/* Created date */}
      {entity.created_at && (
        <div className="flex items-start">
          <span className="text-xs text-gray-500 w-20">Created:</span>
          <span className="text-sm text-gray-700">{formatDateTime(entity.created_at)}</span>
        </div>
      )}

      {/* Updated date */}
      {entity.updated_at && (
        <div className="flex items-start">
          <span className="text-xs text-gray-500 w-20">Updated:</span>
          <span className="text-sm text-gray-700">{formatDateTime(entity.updated_at)}</span>
        </div>
      )}

      {/* Summary */}
      {entity.summary && (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Summary
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">{entity.summary}</p>
        </div>
      )}

      {/* Labels */}
      {entity.labels && entity.labels.length > 0 && (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Labels
          </p>
          <div className="flex flex-wrap gap-2">
            {entity.labels.map((label) => (
              <span
                key={label}
                className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600"
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Attributes */}
      {entity.attributes && Object.keys(entity.attributes).length > 0 && (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Properties
          </p>
          <div className="space-y-2">
            {Object.entries(entity.attributes).map(([key, value]) => (
              <div key={key} className="flex items-start">
                <span className="text-xs text-gray-500 w-24 font-mono">{key}:</span>
                <span className="text-sm text-gray-700 flex-1 break-all">
                  {value !== null && value !== undefined ? String(value) : 'None'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Edge details component
function EdgeDetails({
  edge,
  toggleSelfLoop,
  expandedSelfLoops,
  closeDetailPanel,
}: {
  edge: EntityEdge | SelfLoopGroup
  toggleSelfLoop: (id: string) => void
  expandedSelfLoops: Set<string>
  closeDetailPanel: () => void
}) {
  // Check if this is a self-loop group
  if ('isSelfLoopGroup' in edge && edge.isSelfLoopGroup) {
    return (
      <div className="space-y-3">
        <div className="bg-green-50 border border-green-100 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-900">
              {edge.source_name} - Self Relations
            </span>
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
              {edge.selfLoopCount} items
            </span>
          </div>
        </div>

        <div className="space-y-2">
          {edge.selfLoopEdges.map((loop, idx) => {
            const loopId = loop.uuid || `loop-${idx}`
            const isExpanded = expandedSelfLoops.has(loopId)

            return (
              <div
                key={loopId}
                className={`border border-gray-200 rounded-lg overflow-hidden ${isExpanded ? 'bg-gray-50' : ''}`}
              >
                <button
                  onClick={() => toggleSelfLoop(loopId)}
                  className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-100"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-gray-500">#{idx + 1}</span>
                    <span className="text-sm text-gray-900 truncate max-w-[180px]">
                      {loop.name || loop.fact_type || 'RELATED'}
                    </span>
                  </div>
                  <span className="text-gray-400">{isExpanded ? '−' : '+'}</span>
                </button>

                {isExpanded && (
                  <div className="px-3 pb-3 text-sm space-y-2 border-t border-gray-100">
                    {loop.uuid && (
                      <div className="flex items-start">
                        <span className="text-xs text-gray-500 w-16">UUID:</span>
                        <span className="font-mono text-xs text-gray-600 break-all flex-1">
                          {loop.uuid}
                        </span>
                      </div>
                    )}
                    {loop.fact && (
                      <div className="flex items-start">
                        <span className="text-xs text-gray-500 w-16">Fact:</span>
                        <span className="text-gray-700 flex-1">{loop.fact}</span>
                      </div>
                    )}
                    {loop.fact_type && (
                      <div className="flex items-start">
                        <span className="text-xs text-gray-500 w-16">Type:</span>
                        <span className="text-gray-700">{loop.fact_type}</span>
                      </div>
                    )}
                    {loop.created_at && (
                      <div className="flex items-start">
                        <span className="text-xs text-gray-500 w-16">Created:</span>
                        <span className="text-gray-700">{formatDateTime(loop.created_at)}</span>
                      </div>
                    )}
                    {loop.episodes && loop.episodes.length > 0 && (
                      <div className="flex items-start">
                        <span className="text-xs text-gray-500 w-16">Episodes:</span>
                        <div className="flex flex-wrap gap-1 flex-1">
                          {loop.episodes.map((ep) => (
                            <span
                              key={ep}
                              className="px-2 py-0.5 bg-gray-100 rounded text-[10px] font-mono text-gray-600"
                            >
                              {ep}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // Regular edge
  const regularEdge = edge as EntityEdge
  return (
    <div className="space-y-3">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
        <p className="text-sm font-medium text-gray-900">
          {regularEdge.source_name || 'Source'} →{' '}
          {regularEdge.name || regularEdge.fact_type || 'RELATED'} →{' '}
          {regularEdge.target_name || 'Target'}
        </p>
      </div>

      {regularEdge.uuid && (
        <div className="flex items-start">
          <span className="text-xs text-gray-500 w-16">UUID:</span>
          <span className="font-mono text-xs text-gray-600 break-all flex-1">
            {regularEdge.uuid}
          </span>
        </div>
      )}

      {regularEdge.name && (
        <div className="flex items-start">
          <span className="text-xs text-gray-500 w-16">Label:</span>
          <span className="text-gray-700">{regularEdge.name}</span>
        </div>
      )}

      {regularEdge.fact_type && (
        <div className="flex items-start">
          <span className="text-xs text-gray-500 w-16">Type:</span>
          <span className="text-gray-700">{regularEdge.fact_type}</span>
        </div>
      )}

      {regularEdge.fact && (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Fact
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">{regularEdge.fact}</p>
        </div>
      )}

      {regularEdge.episodes && regularEdge.episodes.length > 0 && (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Episodes
          </p>
          <div className="flex flex-wrap gap-2">
            {regularEdge.episodes.map((ep) => (
              <span
                key={ep}
                className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-xs font-mono text-gray-600"
              >
                {ep}
              </span>
            ))}
          </div>
        </div>
      )}

      {regularEdge.created_at && (
        <div className="pt-3 border-t border-gray-100 flex items-start">
          <span className="text-xs text-gray-500 w-16">Created:</span>
          <span className="text-gray-700">{formatDateTime(regularEdge.created_at)}</span>
        </div>
      )}

      {regularEdge.valid_at && (
        <div className="pt-3 border-t border-gray-100 flex items-start">
          <span className="text-xs text-gray-500 w-16">Valid From:</span>
          <span className="text-gray-700">{formatDateTime(regularEdge.valid_at)}</span>
        </div>
      )}
    </div>
  )
}
