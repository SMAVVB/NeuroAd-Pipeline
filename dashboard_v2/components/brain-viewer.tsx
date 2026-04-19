'use client'

import { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'

// OrbitControls type - imported dynamically at runtime
type OrbitControls = any

// ROI mapping based on neuroscientific knowledge
// Mapping per issue requirements:
// neural_engagement→prefrontal, emotional_impact→limbic, face_response→temporal,
// scene_response→occipital, motion_response→MT, language_engagement→frontal/broca
const ROI_CONFIG = {
  prefrontal: {
    name: 'Prefrontal Cortex',
    color: '#3b82f6', // blue
    position: { x: 0, y: 0.15, z: -0.4 },
    scale: { x: 0.3, y: 0.25, z: 0.25 },
    label: 'Neural Engagement',
  },
  limbic: {
    name: 'Limbic System',
    color: '#3b82f6', // blue
    position: { x: 0, y: -0.1, z: 0.0 },
    scale: { x: 0.25, y: 0.2, z: 0.2 },
    label: 'Emotional Impact',
  },
  temporal: {
    name: 'Temporal Lobe',
    color: '#3b82f6', // blue
    position: { x: 0.45, y: -0.05, z: 0.0 },
    scale: { x: 0.25, y: 0.2, z: 0.25 },
    label: 'Face Response',
  },
  occipital: {
    name: 'Occipital Lobe',
    color: '#3b82f6', // blue
    position: { x: 0, y: -0.1, z: 0.55 },
    scale: { x: 0.25, y: 0.2, z: 0.25 },
    label: 'Scene Response',
  },
  mt: {
    name: 'MT Area',
    color: '#3b82f6', // blue
    position: { x: 0.3, y: -0.15, z: 0.35 },
    scale: { x: 0.2, y: 0.2, z: 0.2 },
    label: 'Motion Response',
  },
  frontal: {
    name: 'Frontal Lobe / Broca',
    color: '#3b82f6', // blue
    position: { x: -0.25, y: 0.1, z: -0.2 },
    scale: { x: 0.25, y: 0.15, z: 0.2 },
    label: 'Language Engagement',
  },
}

// ROI mapping from tribe scores to brain regions
const ROI_NAMES = ['prefrontal', 'limbic', 'temporal', 'occipital', 'mt', 'frontal'] as const
type ROIName = typeof ROI_NAMES[number]

export const TRIBE_ROI_MAPPING: Record<string, ROIName> = {
  neural_engagement: 'prefrontal',
  emotional_impact: 'limbic',
  face_response: 'temporal',
  scene_response: 'occipital',
  motion_response: 'mt',
  language_engagement: 'frontal',
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
  const brainGroupRef = useRef<THREE.Group | null>(null)
  const roiSpheresRef = useRef<THREE.Mesh[]>([])
  const controlsRef = useRef<any | null>(null)
  const animationRef = useRef<number | undefined>(undefined)
  const isDraggingRef = useRef(false)

  // Create stylized brain using geometries
  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x1a1a1a) // dark grey instead of black
    sceneRef.current = scene

    // Camera - slightly from top
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0.5, 3.0)

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.setClearColor(0x1a1a1a, 0) // dark grey instead of black
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

    // Create stylized brain from multiple geometries
    const brainGroup = new THREE.Group()
    scene.add(brainGroup)

    // Main brain shape - two hemispheres with realistic proportions
    // Left hemisphere (abgeflachter Ellipsoid: ScaleY 0.75, ScaleZ 1.2)
    const leftHemisphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.6, 32, 32),
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.4,
        metalness: 0.1,
      })
    )
    leftHemisphere.position.set(-0.32, 0, 0) // slight gap in the middle
    leftHemisphere.scale.set(1, 0.75, 1.2)
    brainGroup.add(leftHemisphere)

    // Right hemisphere (abgeflachter Ellipsoid: ScaleY 0.75, ScaleZ 1.2)
    const rightHemisphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.6, 32, 32),
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.4,
        metalness: 0.1,
      })
    )
    rightHemisphere.position.set(0.32, 0, 0) // slight gap in the middle
    rightHemisphere.scale.set(1, 0.75, 1.2)
    brainGroup.add(rightHemisphere)

    // Cerebellum (Kleinhirn) - small sphere at back-bottom
    const cerebellum = new THREE.Mesh(
      new THREE.SphereGeometry(0.4, 32, 32),
      new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: 0.4, metalness: 0.1 })
    )
    cerebellum.position.set(0, -0.2, 0.7)
    brainGroup.add(cerebellum)

    // Brain Stem - narrow cylinder at bottom
    const brainStem = new THREE.Mesh(
      new THREE.CylinderGeometry(0.1, 0.15, 0.4, 16),
      new THREE.MeshStandardMaterial({ color: 0xe0e0e0, roughness: 0.4, metalness: 0.1 })
    )
    brainStem.position.set(0, -0.5, 0.6)
    brainStem.rotation.x = Math.PI / 2 // align with Z axis
    brainGroup.add(brainStem)

    brainGroupRef.current = brainGroup

    // Create ROI spheres (half-transparent for brain shape visibility)
    Object.entries(ROI_CONFIG).forEach(([key, config]) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 32, 32),
        new THREE.MeshStandardMaterial({
          color: config.color,
          emissive: config.color,
          emissiveIntensity: 0.3,
          roughness: 0.2,
          metalness: 0.5,
          transparent: true,
          opacity: 0.85, // half-transparent
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

    // Dynamic import of OrbitControls
    const loadAndInitControls = async () => {
      const OrbitControls = (await import('three/examples/jsm/controls/OrbitControls' as any)).OrbitControls as any
      const controls = new OrbitControls(camera, renderer.domElement)
      controls.enableDamping = true
      controls.dampingFactor = 0.05
      controls.minDistance = 2
      controls.maxDistance = 6
      controlsRef.current = controls
    }

    loadAndInitControls()

    // Handle rotation
    let rotationSpeed = 0.002
    let targetRotationY = 0

    const animate = () => {
      animationRef.current = requestAnimationFrame(animate)

      if (!isDraggingRef.current) {
        targetRotationY += rotationSpeed
        brainGroup.rotation.y = targetRotationY
      }

      controlsRef.current?.update(null)
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
      renderer.dispose()
    }
  }, [])

  // Update ROI colors based on scores
  useEffect(() => {
    roiSpheresRef.current.forEach(sphere => {
      const roiKey = sphere.userData.roiKey as string
      const scoreKey = roiKey as keyof typeof tribeScores
      const score = tribeScores[scoreKey] ?? 0
      const color = getScoreColor(score)

      // Type assertion for MeshStandardMaterial
      const material = sphere.material as THREE.MeshStandardMaterial
      material.color.set(color)
      material.emissive.set(color)
      material.emissiveIntensity = score > 0.18 ? 0.3 : 0.15
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
