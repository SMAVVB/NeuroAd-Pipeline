import React from 'react';
import MetricBar from '../components/MetricBar';
import { viNetScores, calculateGrade } from '../data/scores';

const ViNetPage = () => {
  // Heatmap placeholder - in real app would display actual heatmap image
  const HeatmapPlaceholder = () => (
    <div style={styles.heatmapContainer}>
      <div style={styles.heatmapGrid}>
        {Array.from({ length: 8 }).map((_, row) => (
          <div key={row} style={styles.heatmapRow}>
            {Array.from({ length: 8 }).map((_, col) => {
              // Create a center-biased gradient pattern
              const centerX = 3.5;
              const centerY = 3.5;
              const distance = Math.sqrt((col - centerX) ** 2 + (row - centerY) ** 2);
              const intensity = Math.max(0, 1 - distance / 5);
              const opacity = Math.min(1, intensity * (1 - viNetScores.centerBias * 0.5) + viNetScores.centerBias * 0.3);
              return (
                <div
                  key={`${row}-${col}`}
                  style={{
                    ...styles.heatmapCell,
                    opacity,
                    backgroundColor: opacity > 0.5 ? '#6366F1' : opacity > 0.2 ? '#3B82F6' : '#1E40AF'
                  }}
                />
              );
            })}
          </div>
        ))}
      </div>
      <div style={styles.heatmapOverlay}>
        <div style={styles.heatmapOverlayInner}>
          <span style={styles.heatmapLabel}>Heatmap Preview</span>
        </div>
      </div>
    </div>
  );

  // Calculate attention distribution percentages
  const totalAttention = viNetScores.productAttention + viNetScores.brandAttention + viNetScores.ctaAttention;
  const productPct = totalAttention > 0 ? (viNetScores.productAttention / totalAttention) * 100 : 0;
  const brandPct = totalAttention > 0 ? (viNetScores.brandAttention / totalAttention) * 100 : 0;
  const ctaPct = totalAttention > 0 ? (viNetScores.ctaAttention / totalAttention) * 100 : 0;

  return (
    <div style={styles.container}>
      <div style={styles.intro}>
        <h2 style={styles.introTitle}>ViNet Attention Analysis</h2>
        <p style={styles.introText}>
          ViNet analyzes where viewers look and whether they see the right things.
          Our saliency model predicts visual attention patterns based on human
          eye-tracking data and deep learning.
        </p>
      </div>

      {/* Heatmap */}
      <div style={styles.heatmapSection}>
        <h3 style={styles.sectionTitle}>Attention Heatmap</h3>
        <p style={styles.sectionSubtitle}>
          Visual representation of predicted attention distribution across the frame.
          Warmer colors indicate higher predicted attention.
        </p>
        <HeatmapPlaceholder />
        <div style={styles.heatmapCaption}>
          <p style={styles.captionText}>
            Note: Actual saliency heatmap would be displayed here from
            <code style={styles.code}> campaigns/apple_vs_samsung/scores/apple_iphone17pro_ultimate_saliency_heatmap.png </code>
          </p>
        </div>
      </div>

      {/* Attention Distribution */}
      <div style={styles.distributionSection}>
        <h3 style={styles.sectionTitle}>Attention Distribution</h3>
        <p style={styles.sectionSubtitle}>
          Where viewers are looking and what they're noticing
        </p>
        <div style={styles.distributionGrid}>
          <div style={styles.attentionItem}>
            <div style={styles.attentionIcon}>📦</div>
            <div style={styles.attentionInfo}>
              <span style={styles.attentionLabel}>Product Attention</span>
              <span style={styles.attentionValue}>{(viNetScores.productAttention * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div style={styles.attentionItem}>
            <div style={styles.attentionIcon}>🏷️</div>
            <div style={styles.attentionInfo}>
              <span style={styles.attentionLabel}>Brand Attention</span>
              <span style={styles.attentionValue}>{(viNetScores.brandAttention * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div style={styles.attentionItem}>
            <div style={styles.attentionIcon}>👉</div>
            <div style={styles.attentionInfo}>
              <span style={styles.attentionLabel}>CTA Attention</span>
              <span style={styles.attentionValue}>{(viNetScores.ctaAttention * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Center Bias Indicator */}
      <div style={styles.biasSection}>
        <h3 style={styles.sectionTitle}>Center Bias Indicator</h3>
        <p style={styles.sectionSubtitle}>
          Measures how much attention is concentrated in the center of the frame
        </p>
        <div style={styles.biasContainer}>
          <div style={styles.biasCircle}>
            <div
              style={{
                ...styles.biasInner,
                opacity: viNetScores.centerBias
              }}
            />
            <div style={styles.biasRing} />
          </div>
          <div style={styles.biasValues}>
            <div style={styles.biasValueItem}>
              <span style={styles.biasLabel}>Center Bias</span>
              <span style={{ ...styles.biasNumber, color: viNetScores.centerBias > 0.8 ? '#EF4444' : '#10B981' }}>
                {viNetScores.centerBias.toFixed(2)}
              </span>
            </div>
            <div style={styles.biasValueItem}>
              <span style={styles.biasLabel}>Temporal Variance</span>
              <span style={{ ...styles.biasNumber, color: viNetScores.temporalVariance > 0.5 ? '#10B981' : '#F59E0B' }}>
                {viNetScores.temporalVariance.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Strengths and Weaknesses */}
      <div style={styles.analysisSection}>
        <div style={styles.analysisGrid}>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Strengths</h4>
            <ul style={styles.list}>
              {viNetScores.strengths?.map((item, index) => (
                <li key={index} style={styles.listItem}>{item}</li>
              ))}
            </ul>
          </div>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Weaknesses</h4>
            <ul style={styles.list}>
              {viNetScores.weaknesses?.map((item, index) => (
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
          {viNetScores.recommendations?.map((rec, index) => (
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
  heatmapSection: {
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
  heatmapContainer: {
    position: 'relative',
    backgroundColor: '#1A1A1A',
    borderRadius: '0',
    border: '1px solid #333333',
    overflow: 'hidden'
  },
  heatmapGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(8, 1fr)',
    aspectRatio: '16/9',
    width: '100%',
    maxWidth: '800px'
  },
  heatmapRow: {
    display: 'flex'
  },
  heatmapCell: {
    flex: 1,
    transition: 'opacity 0.3s ease'
  },
  heatmapOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0) 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  heatmapOverlayInner: {
    padding: '16px 32px',
    backgroundColor: 'rgba(0,0,0,0.8)',
    borderRadius: '0',
    border: '1px solid #333333'
  },
  heatmapLabel: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#FFFFFF'
  },
  heatmapCaption: {
    padding: '16px',
    backgroundColor: '#1A1A1A',
    borderRadius: '0',
    border: '1px solid #333333',
    marginTop: '16px'
  },
  captionText: {
    margin: 0,
    fontSize: '12px',
    color: '#6B7280',
    fontFamily: '"Inter", sans-serif'
  },
  code: {
    fontFamily: '"JetBrains Mono", monospace',
    color: '#6366F1'
  },
  distributionSection: {
    marginBottom: '48px'
  },
  distributionGrid: {
    display: 'flex',
    gap: '24px'
  },
  attentionItem: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    padding: '24px',
    borderRadius: '0',
    border: '1px solid #333333',
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  attentionIcon: {
    fontSize: '32px'
  },
  attentionInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  attentionLabel: {
    fontSize: '14px',
    color: '#9CA3AF'
  },
  attentionValue: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#FFFFFF',
    fontFamily: '"JetBrains Mono", monospace'
  },
  biasSection: {
    marginBottom: '48px'
  },
  biasContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '48px'
  },
  biasCircle: {
    position: 'relative',
    width: '150px',
    height: '150px'
  },
  biasInner: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '100%',
    height: '100%',
    backgroundColor: '#6366F1',
    borderRadius: '50%',
    transition: 'opacity 0.5s ease'
  },
  biasRing: {
    position: 'absolute',
    top: '0',
    left: '0',
    width: '100%',
    height: '100%',
    border: '2px solid #6366F1',
    borderRadius: '50%',
    opacity: 0.5
  },
  biasValues: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px'
  },
  biasValueItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  biasLabel: {
    fontSize: '12px',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  biasNumber: {
    fontSize: '24px',
    fontWeight: '700',
    fontFamily: '"JetBrains Mono", monospace'
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

export default ViNetPage;
