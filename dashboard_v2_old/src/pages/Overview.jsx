import React from 'react';
import { useNavigate } from 'react-router-dom';
import ScoreCard from '../components/ScoreCard';
import MetricBar from '../components/MetricBar';
import { campaignData, tribeScores, miroFishScores, clipScores, viNetScores, calculateGrade } from '../data/scores';

const Overview = () => {
  const navigate = useNavigate();

  const getModuleScore = (moduleId) => {
    switch (moduleId) {
      case 'tribe':
        return (tribeScores.neuralEngagement + tribeScores.emotionalImpact + tribeScores.faceResponse) / 3;
      case 'mirofish':
        return (miroFishScores.viralityScore + miroFishScores.positiveSentiment) / 2;
      case 'clip':
        return clipScores.brandMatchScore;
      case 'vinet':
        return 1 - viNetScores.centerBias;
      default:
        return 0;
    }
  };

  const creativeRankings = campaignData.creativeRankings.overall.map((creative, index) => {
    const name = creative.split('/').pop().replace('.mp4', '');
    return {
      rank: index + 1,
      name,
      tribe: getModuleScore('tribe'),
      mirofish: getModuleScore('mirofish'),
      clip: getModuleScore('clip'),
      vinet: getModuleScore('vinet')
    };
  });

  const handleRankingClick = (creativePath) => {
    // For now, just log the selection
    console.log('Selected creative:', creativePath);
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>{campaignData.name}</h1>
        <div style={styles.headerMeta}>
          <span style={styles.brand}>{campaignData.brand}</span>
          <span style={styles.date}>Generated: 2026-04-15</span>
        </div>
      </div>

      {/* Main Score Cards */}
      <div style={styles.scoreGrid}>
        <ScoreCard
          title="TRIBE Neural"
          score={getModuleScore('tribe')}
          grade={calculateGrade(getModuleScore('tribe'))}
          subtitle="Neural engagement and emotional impact analysis"
          color="#6366F1"
        />
        <ScoreCard
          title="MiroFish Social"
          score={getModuleScore('mirofish')}
          grade={calculateGrade(getModuleScore('mirofish'))}
          subtitle="Social media response simulation"
          color="#3B82F6"
        />
        <ScoreCard
          title="CLIP Brand"
          score={getModuleScore('clip')}
          grade={calculateGrade(getModuleScore('clip'))}
          subtitle="Brand consistency and identity analysis"
          color="#8B5CF6"
        />
        <ScoreCard
          title="ViNet Attention"
          score={getModuleScore('vinet')}
          grade={calculateGrade(getModuleScore('vinet'))}
          subtitle="Visual attention and saliency mapping"
          color="#EC4899"
        />
      </div>

      {/* Creative Ranking Table */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Creative Ranking</h2>
        <div style={styles.rankingTable}>
          <div style={styles.rankingHeader}>
            <span style={styles.rankHeader}>Rank</span>
            <span style={styles.nameHeader}>Creative</span>
            <span style={styles.scoreHeader}>Overall</span>
          </div>
          {creativeRankings.map((creative) => (
            <div
              key={creative.rank}
              style={styles.rankingRow}
              onClick={() => handleRankingClick(creative.rank === 1 ? campaignData.creativeRankings.overall[0] : '')}
            >
              <span style={styles.rank}>{creative.rank}</span>
              <span style={styles.name}>{creative.name.replace('apple_', '').replace('_', ' ')}</span>
              <span style={styles.score}>{((creative.tribe + creative.mirofish + creative.clip + creative.vinet) / 4 * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Key Recommendations */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Key Recommendations</h2>
        <div style={styles.recommendations}>
          {campaignData.recommendations.map((rec, index) => (
            <div key={index} style={styles.recommendationItem}>
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
  header: {
    marginBottom: '48px'
  },
  title: {
    margin: '0 0 8px 0',
    fontSize: '36px',
    fontWeight: '700',
    letterSpacing: '-0.02em'
  },
  headerMeta: {
    display: 'flex',
    gap: '24px',
    alignItems: 'center'
  },
  brand: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  date: {
    fontSize: '14px',
    color: '#6B7280',
    fontFamily: '"JetBrains Mono", monospace'
  },
  scoreGrid: {
    display: 'flex',
    gap: '24px',
    marginBottom: '48px'
  },
  section: {
    marginBottom: '48px'
  },
  sectionTitle: {
    margin: '0 0 24px 0',
    fontSize: '18px',
    fontWeight: '600',
    color: '#FFFFFF',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    borderBottom: '1px solid #333333',
    paddingBottom: '12px'
  },
  rankingTable: {
    backgroundColor: '#1A1A1A',
    borderRadius: '0'
  },
  rankingHeader: {
    display: 'flex',
    padding: '16px 24px',
    backgroundColor: '#27272a',
    fontWeight: '600',
    fontSize: '12px',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  rankHeader: {
    flex: '0 0 80px'
  },
  nameHeader: {
    flex: 1
  },
  scoreHeader: {
    flex: '0 0 120px',
    textAlign: 'right'
  },
  rankingRow: {
    display: 'flex',
    padding: '16px 24px',
    borderBottom: '1px solid #333333',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease'
  },
  rank: {
    flex: '0 0 80px',
    fontFamily: '"JetBrains Mono", monospace',
    color: '#6B7280'
  },
  name: {
    flex: 1,
    fontFamily: '"Inter", sans-serif'
  },
  score: {
    flex: '0 0 120px',
    textAlign: 'right',
    fontFamily: '"JetBrains Mono", monospace',
    fontWeight: '600'
  },
  recommendations: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0'
  },
  recommendationItem: {
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

export default Overview;
