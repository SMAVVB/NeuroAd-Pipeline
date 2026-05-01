import React from 'react';
import { calculateGrade } from '../data/scores';

const ScoreCard = ({ title, score, grade, subtitle, color = '#6366F1' }) => {
  const gradeData = grade || calculateGrade(score);

  return (
    <div style={{ ...styles.card, borderLeft: `4px solid ${color}` }}>
      <div style={styles.header}>
        <h3 style={styles.title}>{title}</h3>
        <span style={{ ...styles.grade, color: gradeData.color }}>
          {gradeData.grade}
        </span>
      </div>

      <div style={styles.scoreContainer}>
        <span style={styles.score}>{(score * 100).toFixed(0)}</span>
        <span style={styles.scoreLabel}>Score</span>
      </div>

      {subtitle && <p style={styles.subtitle}>{subtitle}</p>}

      <div style={styles.progressBar}>
        <div
          style={{
            ...styles.progressFill,
            width: `${Math.min(score * 100, 100)}%`,
            backgroundColor: color
          }}
        />
      </div>
    </div>
  );
};

const styles = {
  card: {
    backgroundColor: '#F5F5F5',
    padding: '24px',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    borderRadius: '0'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px'
  },
  title: {
    margin: 0,
    fontSize: '14px',
    fontWeight: '600',
    color: '#374151',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  grade: {
    fontSize: '20px',
    fontWeight: '700',
    fontFamily: '"JetBrains Mono", monospace'
  },
  scoreContainer: {
    display: 'flex',
    alignItems: 'baseline',
    marginBottom: '8px'
  },
  score: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#111827',
    fontFamily: '"JetBrains Mono", monospace',
    marginRight: '8px'
  },
  scoreLabel: {
    fontSize: '12px',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  subtitle: {
    margin: '0 0 16px 0',
    fontSize: '13px',
    color: '#4B5563',
    lineHeight: '1.5'
  },
  progressBar: {
    height: '4px',
    backgroundColor: '#E5E7EB',
    borderRadius: '0',
    overflow: 'hidden',
    flex: 1
  },
  progressFill: {
    height: '100%',
    borderRadius: '0',
    transition: 'width 0.5s ease'
  }
};

export default ScoreCard;
