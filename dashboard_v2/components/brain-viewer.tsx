'use client'

import { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

// ROI mapping based on neuroscientific knowledge
// Mapping: neural_engagement→prefrontal, emotional_impact→TPJ, face_response→FFA, scene_response→PPA, motion_response→MT, language_engagement→Broca
const ROI_CONFIG = {
  prefrontal: {
    name: 'Prefrontal Cortex',
    color: '#3b82f6', // blue
    position: { x: 0, y: 0.6, z: 0.2 },
    scale: { x: 0.35, y: 0.25, z: 0.3 },
    label: 'Neural Engagement',
  },
  tpj: {
    name: 'TPJ',
    color: '#3b82f6', // blue
    position: { x: 0.35, y: 0.1, z: 0.2 },
    scale: { x: 0.2, y: 0.2, z: 0.2 },
    label: 'Emotional Impact',
  },
  ffa: {
    name: 'FFA',
    color: '#3b82f6', // blue
    position: { x: 0.35, y: -0.1, z: 0.5 },
    scale: { x: 0.2, y: 0.2, z: 0.2 },
    label: 'Face Response',
  },
  ppa: {
    name: 'PPA',
    color: '#3b82f6', // blue
    position: { x: -0.35, y: -0.1, z: 0.5 },
    scale: { x: 0.2, y: 0.2, z: 0.2 },
    label: 'Scene Response',
  },
  mt: {
    name: 'MT',
    color: '#3b82f6', // blue
    position: { x: -0.3, y: -0.3, z: 0.4 },
    scale: { x: 0.2, y: 0.2, z: 0.2 },
    label: 'Motion Response',
  },
  broca: {
    name: 'Broca Area',
    color: '#3b82f6', // blue
    position: { x: 0, y: -0.1, z: 0.8 },
    scale: { x: 0.25, y: 0.15, z: 0.2 },
    label: 'Language Engagement',
  },
}

// ROI mapping from tribe scores to brain regions
export const TRIBE_ROI_MAPPING: Record<string, keyof typeof ROI_CONFIG> = {
  neural_engagement: 'prefrontal',
  emotional_impact: 'tpj',
  face_response: 'ffa',
  scene_response: 'ppa',
  motion_response: 'mt',
  language_engagement: 'broca',
}

function getScoreColor(score: number): string {
  // low=blau, mittel=gelb, hoch=grün
  if (score >= 0.2) return '#10b981' // green (high)
  if (score >= 0.18) return '#f59e0b' // yellow (medium)
  return '#3b82f6' // blue (low)
}

interface BrainViewerProps {
  tribeScores: {
    neural_engagement: number
    emotional_impact: number
    face_response: number
    scene_response: number
    motion_response: number
    language_engagement: number
  }
  size?: 'sm' | 'md' | 'lg'
}

export function BrainViewer({ tribeScores, size = 'md' }: BrainViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const brainMeshRef = useRef<THREE.Mesh | null>(null)
  const roiSpheresRef = useRef<THREE.Mesh[]>([])
  const controlsRef = useRef<OrbitControls | null>(null)
  const animationRef = useRef<number>()
  const isDraggingRef = useRef(false)

  // Create stylized brain using geometries
  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a0a)
    sceneRef.current = scene

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0, 3.5)

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.setClearColor(0x0a0a0a, 0)
    container.appendChild(renderer.domElement)

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6)
    directionalLight.position.set(5, 5, 5)
    scene.add(directionalLight)

    const backLight = new THREE.DirectionalLight(0xffffff, 0.3)
    backLight.position.set(-5, -5, -5)
    scene.add(backLight)

    // Create stylized brain from multiple spheres (no external mesh needed)
    const brainGroup = new THREE.Group()
    scene.add(brainGroup)

    // Main brain shape - two hemispheres
    const hemisphereGeo = new THREE.SphereGeometry(0.6, 32, 32)

    // Left hemisphere
    const leftHemisphere = new THREE.Mesh(hemisphereGeo, new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.4,
      metalness: 0.1,
    }))
    leftHemisphere.position.x = -0.35
    brainGroup.add(leftHemisphere)

    // Right hemisphere
    const rightHemisphere = new THREE.Mesh(hemisphereGeo, new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.4,
      metalness: 0.1,
    }))
    rightHemisphere.position.x = 0.35
    brainGroup.add(rightHemisphere)

    // Frontal lobe connector
    const frontalConnector = new THREE.Mesh(
      new THREE.SphereGeometry(0.25, 32, 32),
      new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4, metalness: 0.1 })
    )
    frontalConnector.position.set(0, 0.2, 0.4)
    brainGroup.add(frontalConnector)

    // Occipital lobe (back)
    const occipitalLobe = new THREE.Mesh(
      new THREE.SphereGeometry(0.3, 32, 32),
      new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4, metalness: 0.1 })
    )
    occipitalLobe.position.set(0, -0.1, 0.75)
    brainGroup.add(occipitalLobe)

    brainMeshRef.current = brainGroup

    // Create ROI spheres
    Object.entries(ROI_CONFIG).forEach(([key, config]) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 32, 32),
        new THREE.MeshStandardMaterial({
          color: config.color,
          emissive: config.color,
          emissiveIntensity: 0.3,
          roughness: 0.2,
          metalness: 0.5,
        })
      )
      sphere.position.set(
        config.position.x,
        config.position.y,
        config.position.z
      )
      sphere.scale.set(
        config.scale.x,
        config.scale.y,
        config.scale.z
      )
      sphere.userData = { roiKey: key, label: config.label }
      scene.add(sphere)
      roiSpheresRef.current.push(sphere)
    })

    // OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.minDistance = 2
    controls.maxDistance = 6
    controlsRef.current = controls

    // Handle rotation
    let rotationSpeed = 0.002
    let targetRotationY = 0

    const animate = () => {
      animationRef.current = requestAnimationFrame(animate)

      if (!isDraggingRef.current) {
        targetRotationY += rotationSpeed
        brainGroup.rotation.y = targetRotationY
      }

      controls.update()
      renderer.render(scene, camera)
    }

    animate()

    // Handle resize
    const handleResize = () => {
      const newWidth = container.clientWidth
      const newHeight = container.clientHeight
      camera.aspect = newWidth / newHeight
      camera.updateProjectionMatrix()
      renderer.setSize(newWidth, newHeight)
    }

    window.addEventListener('resize', handleResize)

    // Drag state tracking
    const handleDragStart = () => { isDraggingRef.current = true }
    const handleDragEnd = () => { isDraggingRef.current = false }

    renderer.domElement.addEventListener('mousedown', handleDragStart)
    renderer.domElement.addEventListener('touchstart', handleDragStart)
    renderer.domElement.addEventListener('mouseup', handleDragEnd)
    renderer.domElement.addEventListener('touchend', handleDragEnd)
    renderer.domElement.addEventListener('mouseleave', handleDragEnd)

    // Cleanup
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      window.removeEventListener('resize', handleResize)
      renderer.domElement.removeEventListener('mousedown', handleDragStart)
      renderer.domElement.removeEventListener('touchstart', handleDragStart)
      renderer.domElement.removeEventListener('mouseup', handleDragEnd)
      renderer.domElement.removeEventListener('touchend', handleDragEnd)
      renderer.domElement.removeEventListener('mouseleave', handleDragEnd)
      container.removeChild(renderer.domElement)
      scene.dispose()
      renderer.dispose()
    }
  }, [])

  // Update ROI colors based on scores
  useEffect(() => {
    roiSpheresRef.current.forEach(sphere => {
      const roiKey = sphere.userData.roiKey as keyof typeof TRIBE_ROI_MAPPING
      const scoreKey = TRIBE_ROI_MAPPING[roiKey]
      const score = tribeScores[scoreKey] ?? 0
      const color = getScoreColor(score)

      sphere.material.color.set(color)
      sphere.material.emissive.set(color)
      sphere.material.emissiveIntensity = score > 0.18 ? 0.3 : 0.15
    })
  }, [tribeScores])

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden rounded-lg ${size === 'sm' ? 'h-48' : size === 'md' ? 'h-80' : 'h-[500px]'}`}
    />
  )
}

// Helper component to show ROI legend
export function ROILegend() {
  return (
    <div className="flex flex-wrap gap-4 text-xs">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-emerald-500" />
        <span className="text-muted-foreground">High (≥0.20)</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-amber-500" />
        <span className="text-muted-foreground">Medium (0.18)</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-blue-500" />
        <span className="text-muted-foreground">Low (&lt;0.18)</span>
      </div>
    </div>
  )
}
