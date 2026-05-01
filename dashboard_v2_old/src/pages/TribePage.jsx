import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import MetricBar from '../components/MetricBar';
import { tribeScores, calculateGrade } from '../data/scores';

const TRIBEPage = () => {
  const sceneRef = useRef(null);
  const brainContainerRef = useRef(null);

  useEffect(() => {
    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    const camera = new THREE.PerspectiveCamera(75, brainContainerRef.current.clientWidth / 500, 0.1, 1000);
    camera.position.set(0, 0, 15);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(brainContainerRef.current.clientWidth, 500);
    renderer.setPixelRatio(window.devicePixelRatio);
    brainContainerRef.current.appendChild(renderer.domElement);

    // Create simplified brain structure
    const brainGroup = new THREE.Group();

    // Main sphere (cerebrum)
    const cerebrumGeometry = new THREE.SphereGeometry(4, 32, 32);
    const cerebrumMaterial = new THREE.MeshBasicMaterial({
      color: 0x333333,
      wireframe: true
    });
    const cerebrum = new THREE.Mesh(cerebrumGeometry, cerebrumMaterial);
    brainGroup.add(cerebrum);

    // Temporal lobe (face response area) - colored red
    const temporalGeometry = new THREE.SphereGeometry(1.5, 16, 16);
    const temporalMaterial = new THREE.MeshStandardMaterial({
      color: 0xff4444,
      emissive: 0xff0000,
      emissiveIntensity: tribeScores.faceResponse * 0.5,
      wireframe: true
    });
    const temporalLobe = new THREE.Mesh(temporalGeometry, temporalMaterial);
    temporalLobe.position.set(-3, 0, 2);
    brainGroup.add(temporalLobe);

    // Occipital lobe (motion response area) - colored blue
    const occipitalGeometry = new THREE.SphereGeometry(1.5, 16, 16);
    const occipitalMaterial = new THREE.MeshStandardMaterial({
      color: 0x4444ff,
      emissive: 0x0000ff,
      emissiveIntensity: tribeScores.motionResponse * 0.5,
      wireframe: true
    });
    const occipitalLobe = new THREE.Mesh(occipitalGeometry, occipitalMaterial);
    occipitalLobe.position.set(0, 0, -4.5);
    brainGroup.add(occipitalLobe);

    // Frontal lobe (language engagement area) - colored green
    const frontalGeometry = new THREE.SphereGeometry(1.5, 16, 16);
    const frontalMaterial = new THREE.MeshStandardMaterial({
      color: 0x44ff44,
      emissive: 0x00ff00,
      emissiveIntensity: tribeScores.languageEngagement * 0.5,
      wireframe: true
    });
    const frontalLobe = new THREE.Mesh(frontalGeometry, frontalMaterial);
    frontalLobe.position.set(0, 1.5, 3);
    brainGroup.add(frontalLobe);

    scene.add(brainGroup);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 5, 10);
    scene.add(directionalLight);

    const pointLight = new THREE.PointLight(0x6366f1, 0.5);
    pointLight.position.set(-5, 5, 5);
    scene.add(pointLight);

    // Orbit controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);

      // Slow rotation
      brainGroup.rotation.y += 0.005;
      brainGroup.rotation.z += 0.002;

      // Pulsing effects based on scores
      const pulse = Math.sin(Date.now() * 0.002) * 0.1;
      temporalLobe.scale.set(1 + pulse * tribeScores.faceResponse, 1 + pulse * tribeScores.faceResponse, 1 + pulse * tribeScores.faceResponse);

      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      if (brainContainerRef.current) {
        camera.aspect = brainContainerRef.current.clientWidth / 500;
        camera.updateProjectionMatrix();
        renderer.setSize(brainContainerRef.current.clientWidth, 500);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (brainContainerRef.current) {
        brainContainerRef.current.removeChild(renderer.domElement);
      }
      scene.clear();
    };
  }, []);

  const scores = [
    { label: 'Neural Engagement', value: tribeScores.neuralEngagement, color: '#6366F1' },
    { label: 'Emotional Impact', value: tribeScores.emotionalImpact, color: '#8B5CF6' },
    { label: 'Face Response', value: tribeScores.faceResponse, color: '#EF4444' },
    { label: 'Scene Response', value: tribeScores.sceneResponse, color: '#3B82F6' },
    { label: 'Motion Response', value: tribeScores.motionResponse, color: '#06B6D4' },
    { label: 'Language Engagement', value: tribeScores.languageEngagement, color: '#10B981' }
  ];

  return (
    <div style={styles.container}>
      <div style={styles.intro}>
        <h2 style={styles.introTitle}>TRIBE Neural Analysis</h2>
        <p style={styles.introText}>
          TRIBE v2 measures neural responses to visual content. It analyzes how your creative
          activates different brain regions associated with attention, emotion, and memory.
          <br /><br />
          The system tracks six key metrics: neural engagement, emotional impact, face response
          (fusiform face area), scene response, motion response (visual cortex), and language
          engagement (Broca's and Wernicke's areas).
        </p>
      </div>

      {/* 3D Brain Viewer */}
      <div style={styles.brainSection}>
        <h3 style={styles.sectionTitle}>3D Brain Activity Map</h3>
        <p style={styles.sectionSubtitle}>
          Visual representation of brain region activation. Colors indicate different response types:
          <span style={{ color: '#EF4444', fontWeight: '600' }}> Red </span>= Face Response,
          <span style={{ color: '#06B6D4', fontWeight: '600' }}> Blue </span>= Motion Response,
          <span style={{ color: '#10B981', fontWeight: '600' }}> Green </span>= Language Response
        </p>
        <div ref={brainContainerRef} style={styles.brainContainer} />
      </div>

      {/* Engagement Timeline */}
      <div style={styles.timelineSection}>
        <h3 style={styles.sectionTitle}>Engagement Timeline</h3>
        <MetricBar scores={scores} />
      </div>

      {/* Strengths and Weaknesses */}
      <div style={styles.analysisSection}>
        <div style={styles.analysisGrid}>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Strengths</h4>
            <ul style={styles.list}>
              {tribeScores.strengths?.map((item, index) => (
                <li key={index} style={styles.listItem}>{item}</li>
              ))}
            </ul>
          </div>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Weaknesses</h4>
            <ul style={styles.list}>
              {tribeScores.weaknesses?.map((item, index) => (
                <li key={index} style={styles.listItem}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div style={styles.recommendationsSection}>
        <h3 style={styles.sectionTitle}>Recommendations</h3>
        <div style={styles.recommendationsList}>
          {tribeScores.recommendations?.map((rec, index) => (
            <div key={index} style={styles.recommendation}>
              <span style={styles.recNumber}>{index + 1}</span>
              <p style={styles.recText}>{rec}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    flex: 1,
    padding: '40px',
    overflowY: 'auto',
    backgroundColor: '#000000',
    color: '#FFFFFF'
  },
  intro: {
    marginBottom: '48px'
  },
  introTitle: {
    margin: '0 0 12px 0',
    fontSize: '24px',
    fontWeight: '600',
    letterSpacing: '-0.02em'
  },
  introText: {
    margin: 0,
    fontSize: '15px',
    color: '#E5E7EB',
    lineHeight: '1.6'
  },
  brainSection: {
    marginBottom: '48px'
  },
  sectionTitle: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  sectionSubtitle: {
    margin: '0 0 24px 0',
    fontSize: '13px',
    color: '#6B7280',
    lineHeight: '1.6'
  },
  brainContainer: {
    width: '100%',
    position: 'relative'
  },
  timelineSection: {
    marginBottom: '48px'
  },
  analysisSection: {
    marginBottom: '48px'
  },
  analysisGrid: {
    display: 'flex',
    gap: '24px'
  },
  analysisCard: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    padding: '24px',
    borderRadius: '0'
  },
  cardTitle: {
    margin: '0 0 16px 0',
    fontSize: '14px',
    fontWeight: '600',
    color: '#FFFFFF',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  list: {
    margin: 0,
    padding: '0 0 0 16px',
    fontSize: '14px',
    color: '#E5E7EB',
    lineHeight: '1.6'
  },
  listItem: {
    marginBottom: '8px'
  },
  recommendationsSection: {
    marginBottom: '48px'
  },
  recommendationsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0'
  },
  recommendation: {
    display: 'flex',
    alignItems: 'flex-start',
    padding: '16px 0',
    borderBottom: '1px solid #333333'
  },
  recNumber: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#6366F1',
    fontFamily: '"JetBrains Mono", monospace',
    marginRight: '16px',
    minWidth: '24px'
  },
  recText: {
    margin: 0,
    fontSize: '14px',
    color: '#E5E7EB',
    lineHeight: '1.6',
    flex: 1
  }
};

export default TRIBEPage;
