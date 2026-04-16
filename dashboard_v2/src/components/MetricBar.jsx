import React from 'react';

const MetricBar = ({ label, value, max = 1, color = '#6366F1', showValue = true }) => {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div style={styles.container}>
      <div style={styles.labelContainer}>
        <span style={styles.label}>{label}</span>
        {showValue && <span style={styles.value}>{(value * 100).toFixed(0)}%</span>}
      </div>
      <div style={styles.barContainer}>
        <div
          style={{
            ...styles.barFill,
            width: `${percentage}%`,
            backgroundColor: color
          }}
        />
      </div>
    </div>
  );
};

const MetricBarGroup = ({ metrics }) => {
  return (
    <div style={styles.group}>
      {metrics.map((metric, index) => (
        <MetricBar
          key={index}
          label={metric.label}
          value={metric.value}
          max={metric.max}
          color={metric.color}
          showValue={metric.showValue !== false}
        />
      ))}
    </div>
  );
};

const styles = {
  container: {
    marginBottom: '16px'
  },
  labelContainer: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '6px'
  },
  label: {
    fontSize: '13px',
    fontWeight: '500',
    color: '#374151',
    fontFamily: '"Inter", sans-serif'
  },
  value: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#111827',
    fontFamily: '"JetBrains Mono", monospace'
  },
  barContainer: {
    height: '8px',
    backgroundColor: '#E5E7EB',
    borderRadius: '0',
    overflow: 'hidden'
  },
  barFill: {
    height: '100%',
    borderRadius: '0',
    transition: 'width 0.5s ease'
  },
  group: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0'
  }
};

export default MetricBar;
export { MetricBarGroup };
