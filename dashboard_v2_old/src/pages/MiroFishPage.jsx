import React from 'react';
import * as d3 from 'd3-force';
import MetricBar from '../components/MetricBar';
import { miroFishScores } from '../data/scores';

const MiroFishPage = () => {
  const containerRef = React.useRef(null);
  const [agentCount] = React.useState(25);

  // Generate agents with positions based on sentiment
  const generateAgents = () => {
    const agents = [];
    const positiveCount = Math.round(miroFishScores.positiveSentiment * agentCount);
    const negativeCount = Math.round((1 - miroFishScores.positiveSentiment) * agentCount / 2);
    const neutralCount = agentCount - positiveCount - negativeCount;

    for (let i = 0; i < agentCount; i++) {
      let color;
      if (i < positiveCount) {
        color = '#10B981'; // Green for positive
      } else if (i < positiveCount + negativeCount) {
        color = '#EF4444'; // Red for negative
      } else {
        color = '#6B7280'; // Gray for neutral
      }

      agents.push({
        id: i,
        x: Math.random() * 600,
        y: Math.random() * 300,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        color: color,
        size: 6 + Math.random() * 4
      });
    }

    return agents;
  };

  const [agents] = React.useState(generateAgents);

  // Simulate force-directed graph layout
  React.useEffect(() => {
    const simulation = d3.forceSimulation(agents)
      .force('charge', d3.forceManyBody().strength(-30))
      .force('center', d3.forceCenter(300, 150))
      .force('link', d3.forceLink().id(d => d.id).distance(50))
      .force('collide', d3.forceCollide().radius(d => d.size + 2))
      .alphaDecay(0.02);

    simulation.on('tick', () => {
      // Update positions in state would go here in a real implementation
      // For now, we just render the initial positions
    });

    return () => simulation.stop();
  }, [agents]);

  // Generate connections between nearby agents
  const connections = [];
  for (let i = 0; i < agents.length; i++) {
    for (let j = i + 1; j < agents.length; j++) {
      const dx = agents[i].x - agents[j].x;
      const dy = agents[i].y - agents[j].y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (distance < 60) {
        connections.push({
          x1: agents[i].x,
          y1: agents[i].y,
          x2: agents[j].x,
          y2: agents[j].y,
          opacity: 1 - distance / 60
        });
      }
    }
  }

  const gaugeValue = Math.round((miroFishScores.positiveSentiment + miroFishScores.viralityScore) / 2 * 100);

  return (
    <div style={styles.container}>
      <div style={styles.intro}>
        <h2 style={styles.introTitle}>MiroFish Social Analysis</h2>
        <p style={styles.introText}>
          MiroFish simulates how real social media users would react to your creative.
          Our agent network models different audience segments and predicts engagement,
          sentiment, and shareability based on content analysis.
        </p>
      </div>

      {/* Animated Agent Network */}
      <div style={styles.networkSection}>
        <h3 style={styles.sectionTitle}>Animated Agent Network</h3>
        <p style={styles.sectionSubtitle}>
          Visual representation of simulated audience reactions. Green agents indicate positive
          sentiment, red indicates negative, and gray represents neutral responses.
        </p>
        <div style={styles.networkContainer}>
          <svg width="600" height="300" style={styles.networkSvg}>
            {/* Connections */}
            {connections.map((conn, index) => (
              <line
                key={index}
                x1={conn.x1}
                y1={conn.y1}
                x2={conn.x2}
                y2={conn.y2}
                stroke="#374151"
                strokeWidth="1"
                strokeOpacity={conn.opacity * 0.5}
              />
            ))}
            {/* Agents */}
            {agents.map((agent) => (
              <circle
                key={agent.id}
                cx={agent.x}
                cy={agent.y}
                r={agent.size}
                fill={agent.color}
                opacity="0.8"
              />
            ))}
          </svg>
          <div style={styles.legend}>
            <div style={styles.legendItem}>
              <span style={{ ...styles.legendDot, backgroundColor: '#10B981' }} />
              <span>Positive</span>
            </div>
            <div style={styles.legendItem}>
              <span style={{ ...styles.legendDot, backgroundColor: '#EF4444' }} />
              <span>Negative</span>
            </div>
            <div style={styles.legendItem}>
              <span style={{ ...styles.legendDot, backgroundColor: '#6B7280' }} />
              <span>Neutral</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment Gauge */}
      <div style={styles.gaugeSection}>
        <h3 style={styles.sectionTitle}>Sentiment Gauge</h3>
        <div style={styles.gaugeContainer}>
          <div style={styles.gauge}>
            <svg width="200" height="120" viewBox="0 0 200 120">
              {/* Background arc */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="#374151"
                strokeWidth="20"
              />
              {/* Value arc */}
              <path
                d={`M 20 100 A 80 80 0 ${gaugeValue > 50 ? 1 : 0} 1 ${20 + 160 * (gaugeValue / 100)} 100`}
                fill="none"
                stroke={gaugeValue >= 50 ? '#10B981' : '#EF4444'}
                strokeWidth="20"
                strokeLinecap="round"
              />
              {/* Needle */}
              <g transform={`rotate(${gaugeValue * 1.8 - 90} 100 100)`}>
                <line x1="100" y1="100" x2="100" y2="30" stroke="#FFFFFF" strokeWidth="4" />
                <circle cx="100" cy="100" r="8" fill="#FFFFFF" />
              </g>
            </svg>
            <div style={styles.gaugeValue}>
              <span style={styles.gaugeNumber}>{gaugeValue}</span>
              <span style={styles.gaugeLabel}>/ 100</span>
            </div>
          </div>
          <div style={styles.gaugeMetrics}>
            <div style={styles.metric}>
              <span style={styles.metricLabel}>Virality Score</span>
              <span style={styles.metricValue}>{(miroFishScores.viralityScore * 100).toFixed(0)}%</span>
            </div>
            <div style={styles.metric}>
              <span style={styles.metricLabel}>Positive Sentiment</span>
              <span style={styles.metricValue}>{(miroFishScores.positiveSentiment * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Resonance Metrics */}
      <div style={styles.metricsSection}>
        <h3 style={styles.sectionTitle}>Resonance Metrics</h3>
        <div style={styles.metricsGrid}>
          <MetricBar label="Brand Affinity" value={miroFishScores.brandAffinity} color="#6366F1" />
          <MetricBar label="Audience Match" value={miroFishScores.audienceMatch} color="#3B82F6" />
          <MetricBar label="Emotional Resonance" value={miroFishScores.emotionalResonance} color="#8B5CF6" />
          <MetricBar label="Shareability" value={miroFishScores.shareability} color="#EC4899" />
        </div>
      </div>

      {/* Strengths and Weaknesses */}
      <div style={styles.analysisSection}>
        <div style={styles.analysisGrid}>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Strengths</h4>
            <ul style={styles.list}>
              {miroFishScores.strengths?.map((item, index) => (
                <li key={index} style={styles.listItem}>{item}</li>
              ))}
            </ul>
          </div>
          <div style={styles.analysisCard}>
            <h4 style={styles.cardTitle}>Weaknesses</h4>
            <ul style={styles.list}>
              {miroFishScores.weaknesses?.map((item, index) => (
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
          {miroFishScores.recommendations?.map((rec, index) => (
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
  networkSection: {
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
  networkContainer: {
    position: 'relative'
  },
  networkSvg: {
    backgroundColor: '#1A1A1A',
    borderRadius: '0',
    border: '1px solid #333333'
  },
  legend: {
    display: 'flex',
    gap: '24px',
    marginTop: '12px'
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    color: '#E5E7EB'
  },
  legendDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%'
  },
  gaugeSection: {
    marginBottom: '48px'
  },
  gaugeContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '48px'
  },
  gauge: {
    position: 'relative'
  },
  gaugeValue: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -20px)',
    textAlign: 'center'
  },
  gaugeNumber: {
    fontSize: '32px',
    fontWeight: '700',
    fontFamily: '"JetBrains Mono", monospace'
  },
  gaugeLabel: {
    fontSize: '12px',
    color: '#6B7280'
  },
  gaugeMetrics: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px'
  },
  metric: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '13px'
  },
  metricLabel: {
    color: '#9CA3AF'
  },
  metricValue: {
    fontFamily: '"JetBrains Mono", monospace',
    fontWeight: '600'
  },
  metricsSection: {
    marginBottom: '48px'
  },
  metricsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0'
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

export default MiroFishPage;
