import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';
import MetricBar from '../components/MetricBar';
import { clipScores, calculateGrade } from '../data/scores';

const ClipPage = () => {
  // Prepare data for radar chart
  const radarData = [
    { subject: 'Minimalist', A: clipScores.allScores['sleek minimalist design'] * 100, fullMark: 100 },
    { subject: 'Colorful', A: clipScores.allScores['vibrant colorful energy'] * 100, fullMark: 100 },
    { subject: 'Cinematic', A: clipScores.allScores['cinematic storytelling'] * 100, fullMark: 100 },
    { subject: 'Feature', A: clipScores.allScores['feature demonstration'] * 100, fullMark: 100 },
    { subject: 'Emotional', A: clipScores.allScores['emotional lifestyle'] * 100, fullMark: 100 }
  ];

  // Determine brand fit badge
  const brandFit = clipScores.brandMatchScore >= 0.5 ? 'STRONG' : clipScores.brandMatchScore >= 0.3 ? 'OKAY' : 'WEAK';
  const brandFitColor = clipScores.brandMatchScore >= 0.5 ? '#10B981' : clipScores.brandMatchScore >= 0.3 ? '#F59E0B' : '#EF4444';

  const topLabel = clipScores.topLabel.replace(/_/g, ' ');

  return (
    <div style={styles.container}>
      <div style={styles.intro}>
        <h2 style={styles.introTitle}>CLIP Brand Analysis</h2>
        <p style={styles.introText}>
          CLIP analyzes how well your creative aligns with your brand identity.
          Our model evaluates visual content against five key brand dimensions:
          minimalist design, colorful energy, cinematic storytelling, feature
          demonstration, and emotional lifestyle.
        </p>
      </div>

      {/* Brand Match Radar Chart */}
      <div style={styles.radarSection}>
        <h3 style={styles.sectionTitle}>Brand Match Radar</h3>
        <p style={styles.sectionSubtitle}>
          Visual comparison of your creative against brand dimensions. Larger area
          indicates better brand alignment.
        </p>
        <div style={styles.radarContainer}>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid gridType="circle" stroke="#374151" strokeWidth={1} />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6B7280', fontSize: 10 }} />
              <Radar
                name="Brand Match"
                dataKey="A"
                stroke="#6366F1"
                strokeWidth={2}
                fill="#6366F1"
                fillOpacity={0.3}
              />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Label Score Bars */}
      <div style={styles.labelsSection}>
        <h3 style={styles.sectionTitle}>Label Scores</h3>
        <p style={styles.sectionSubtitle}>
          Individual scores for each brand dimension (0-100% scale)
        </p>
        <div style={styles.labelsGrid}>
          {Object.entries(clipScores.allScores).map(([label, score]) => {
            const isTop = label === clipScores.topLabel;
            return (
              <div key={label} style={{ ...styles.labelItem, ...(isTop ? styles.labelTop : {}) }}>
                <div style={styles.labelHeader}>
                  <span style={styles.labelName}>{label.replace(/_/g, ' ')}</span>
                  {isTop && <span style={styles.labelBadge}>TOP</span>}
                </div>
                <div style={styles.barContainer}>
                  <div
                    style={{
                      ...styles.barFill,
                      width: `${score * 100}%`,
                      backgroundColor: isTop ? '#6366F1' : '#3B82F6'
                    }}
                  />
                </div>
                <span style={styles.scoreValue}>{(score * 100).toFixed(1)}%</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Brand Fit Badge */}
      <div style={styles.fitSection}>
        <h3 style={styles.sectionTitle}>Brand Fit Assessment</h3>
        <div style={styles.fitCard}>
          <div style={{ ...styles.fitBadge, backgroundColor: brandFitColor }}>
            <span style={styles.fitText}>{brandFit}</span>
          </div>
          <div style={styles.fitDetails}>
            <div style={styles.fitDetailItem}>
              <span style={styles.detailLabel}>Brand Match Score</span>
              <span style={styles.detailValue}>{(clipScores.brandMatchScore * 100).toFixed(1)}%</span>
            </div>
            <div style={styles.fitDetailItem}>
              <span style={styles.detailLabel}>Top Label</span>
              <span style={styles.detailValue}>{topLabel}</span>
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
              {clipScores.strengths?.map((item, index) => (
                <li key={index} style={styles.listItem}>{item}</li>
              ))}
            </ul>
          </div>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Weaknesses</h4>
            <ul style={styles.list}>
              {clipScores.weaknesses?.map((item, index) => (
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
          {clipScores.recommendations?.map((rec, index) => (
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
  radarSection: {
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
  radarContainer: {
    backgroundColor: '#1A1A1A',
    padding: '24px',
    borderRadius: '0',
    border: '1px solid #333333'
  },
  labelsSection: {
    marginBottom: '48px'
  },
  labelsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px'
  },
  labelItem: {
    backgroundColor: '#1A1A1A',
    padding: '16px 24px',
    borderRadius: '0',
    border: '1px solid #333333'
  },
  labelTop: {
    borderLeft: '4px solid #6366F1'
  },
  labelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  labelName: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#E5E7EB'
  },
  labelBadge: {
    fontSize: '10px',
    fontWeight: '700',
    color: '#FFFFFF',
    backgroundColor: '#6366F1',
    padding: '2px 8px',
    borderRadius: '0'
  },
  barContainer: {
    height: '6px',
    backgroundColor: '#374151',
    borderRadius: '0',
    marginBottom: '8px',
    overflow: 'hidden'
  },
  barFill: {
    height: '100%',
    borderRadius: '0',
    transition: 'width 0.5s ease'
  },
  scoreValue: {
    fontSize: '12px',
    color: '#6B7280',
    fontFamily: '"JetBrains Mono", monospace'
  },
  fitSection: {
    marginBottom: '48px'
  },
  fitCard: {
    backgroundColor: '#1A1A1A',
    padding: '32px',
    borderRadius: '0',
    border: '1px solid #333333'
  },
  fitBadge: {
    display: 'inline-block',
    padding: '8px 24px',
    borderRadius: '0',
    marginBottom: '24px'
  },
  fitText: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#FFFFFF',
    fontFamily: '"JetBrains Mono", monospace'
  },
  fitDetails: {
    display: 'flex',
    gap: '48px'
  },
  fitDetailItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  detailLabel: {
    fontSize: '12px',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  detailValue: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#FFFFFF',
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

export default ClipPage;
