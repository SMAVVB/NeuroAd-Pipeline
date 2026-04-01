import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

function BrainViewer3D({ scores = {} }) {
  const containerRef = useRef()
  const [hoveredNode, setHoveredNode] = useState(null)
  
  // Default scores if not provided
  const defaultScores = {
    TPJ: 0.18, FFA: 0.21, PPA: 0.20, V5: 0.19, Broca: 0.19, A1: 0.18
  }
  const activeScores = { ...defaultScores, ...scores }

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = null

    const width = container.clientWidth || 600
    const height = 400
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.set(0, 0, 3)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(window.devicePixelRatio)
    container.appendChild(renderer.domElement)

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(5, 5, 5)
    scene.add(directionalLight)

    const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x9ca3af, 0.4)
    scene.add(hemisphereLight)

    // Main brain sphere
    const brainGeometry = new THREE.SphereGeometry(1, 32, 32)
    const brainMaterial = new THREE.MeshPhongMaterial({
      color: 0x262626,
      shininess: 10,
      specular: 0x111111,
    })
    const brainSphere = new THREE.Mesh(brainGeometry, brainMaterial)
    scene.add(brainSphere)

    // ROI regions with hotspots
    const roiData = [
      { name: 'TPJ', phi: 0.3, theta: 2.5, color: 0xdc2626 },
      { name: 'FFA', phi: 1.2, theta: 2.8, color: 0xdc2626 },
      { name: 'PPA', phi: 0.8, theta: 0.8, color: 0xdc2626 },
      { name: 'V5', phi: 0.9, theta: 2.2, color: 0xdc2626 },
      { name: 'Broca', phi: 1.1, theta: 1.2, color: 0xdc2626 },
      { name: 'A1', phi: 1.3, theta: 2.0, color: 0xdc2626 },
    ]

    const hotspotGroup = new THREE.Group()
    scene.add(hotspotGroup)

    const hotspots = roiData.map((roi, index) => {
      const score = activeScores[roi.name] ?? 0
      
      // Calculate position on sphere
      const x = Math.sin(roi.phi) * Math.cos(roi.theta)
      const y = Math.cos(roi.phi)
      const z = Math.sin(roi.phi) * Math.sin(roi.theta)

      // Hotspot sphere
      const hotspotGeometry = new THREE.SphereGeometry(0.15, 16, 16)
      const hotspotMaterial = new THREE.MeshPhongMaterial({
        color: roi.color,
        transparent: true,
        opacity: 0.4 + score * 0.6,
      })
      const hotspot = new THREE.Mesh(hotspotGeometry, hotspotMaterial)
      hotspot.position.set(x, y, z)
      hotspot.userData = { name: roi.name, score: score }
      hotspotGroup.add(hotspot)

      return hotspot
    })

    // Animation loop
    let animationId
    let time = 0

    const animate = () => {
      animationId = requestAnimationFrame(animate)
      time += 0.002

      // Auto-rotate brain
      brainSphere.rotation.y += 0.002
      
      // Rotate hotspotGroup together with brainSphere
      hotspotGroup.rotation.y = brainSphere.rotation.y

      // Pulse hotspots
      hotspots.forEach((hotspot, index) => {
        const score = hotspot.userData.score
        const pulse = Math.sin(time * 2 + index * 0.5) * 0.1 * score
        hotspot.scale.setScalar(1 + pulse)
      })

      renderer.render(scene, camera)
    }

    animate()

    // Handle resize
    const handleResize = () => {
      if (container.clientWidth > 0) {
        camera.aspect = container.clientWidth / 400
        camera.updateProjectionMatrix()
        renderer.setSize(container.clientWidth, 400)
      }
    }

    window.addEventListener('resize', handleResize)

    // Orbit controls (simplified)
    let isDragging = false
    let previousMousePosition = { x: 0, y: 0 }

    const onMouseDown = (e) => {
      isDragging = true
      previousMousePosition = { x: e.offsetX, y: e.offsetY }
    }

    const onMouseMove = (e) => {
      if (isDragging) {
        const deltaX = e.offsetX - previousMousePosition.x
        const deltaY = e.offsetY - previousMousePosition.y

        brainSphere.rotation.y += deltaX * 0.01
        brainSphere.rotation.x += deltaY * 0.01

        previousMousePosition = { x: e.offsetX, y: e.offsetY }
      }
    }

    const onMouseUp = () => {
      isDragging = false
    }

    container.addEventListener('mousedown', onMouseDown)
    container.addEventListener('mousemove', onMouseMove)
    container.addEventListener('mouseup', onMouseUp)
    container.addEventListener('mouseleave', onMouseUp)

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', handleResize)
      container.removeEventListener('mousedown', onMouseDown)
      container.removeEventListener('mousemove', onMouseMove)
      container.removeEventListener('mouseup', onMouseUp)
      container.removeEventListener('mouseleave', onMouseUp)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      scene.clear()
    }
  }, [activeScores])

  // Legend data
  const legendData = [
    { name: 'TPJ', score: activeScores.TPJ ?? 0 },
    { name: 'FFA', score: activeScores.FFA ?? 0 },
    { name: 'PPA', score: activeScores.PPA ?? 0 },
    { name: 'V5', score: activeScores.V5 ?? 0 },
    { name: 'Broca', score: activeScores.Broca ?? 0 },
    { name: 'A1', score: activeScores.A1 ?? 0 },
  ]

  return (
    <div className="flex flex-col gap-4">
      {/* Canvas container */}
      <div ref={containerRef} style={{ width: '100%', height: 400 }} />
      
      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-sm">
        {legendData.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor: '#dc2626',
                opacity: 0.4 + item.score * 0.6,
              }}
            />
            <span className="font-medium">{item.name}</span>
            <span className="font-mono text-secondary">{item.score.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default BrainViewer3D
