import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { campaignData } from '../data/scores';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleCampaignChange = (e) => {
    // For now, only one campaign exists
    // Future: implement campaign switching logic
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'tribe', label: 'TRIBE Neural', icon: '🧠' },
    { id: 'mirofish', label: 'MiroFish Social', icon: '🐟' },
    { id: 'clip', label: 'CLIP Brand', icon: '🎨' },
    { id: 'vinet', label: 'ViNet Attention', icon: '👁️' }
  ];

  return (
    <div style={styles.sidebar}>
      <div style={styles.logo}>
        <h2 style={styles.logoText}>NeuroAd</h2>
      </div>

      <div style={styles.campaignSelector}>
        <label style={styles.label}>Campaign:</label>
        <select
          style={styles.select}
          value={campaignData.id}
          onChange={handleCampaignChange}
        >
          <option value={campaignData.id}>{campaignData.name}</option>
        </select>
      </div>

      <nav style={styles.nav}>
        {navItems.map((item) => (
          <Link
            key={item.id}
            to={`/${item.id}`}
            style={{
              ...styles.navItem,
              ...(location.pathname === `/${item.id}` ? styles.navItemActive : {})
            }}
          >
            <span style={styles.navIcon}>{item.icon}</span>
            <span style={styles.navLabel}>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div style={styles.footer}>
        <p style={styles.footerText}>
          NeuroAd Pipeline v2.0
        </p>
      </div>
    </div>
  );
};

const styles = {
  sidebar: {
    width: '260px',
    height: '100vh',
    backgroundColor: '#1A1A1A',
    color: '#FFFFFF',
    display: 'flex',
    flexDirection: 'column',
    borderRight: '1px solid #333333',
    flexShrink: 0
  },
  logo: {
    padding: '24px 20px',
    borderBottom: '1px solid #333333'
  },
  logoText: {
    margin: 0,
    fontSize: '24px',
    fontWeight: '700',
    letterSpacing: '-0.02em'
  },
  campaignSelector: {
    padding: '16px 20px',
    borderBottom: '1px solid #333333'
  },
  label: {
    display: 'block',
    fontSize: '12px',
    color: '#9CA3AF',
    marginBottom: '8px',
    fontWeight: '500'
  },
  select: {
    width: '100%',
    padding: '8px 12px',
    backgroundColor: '#000000',
    color: '#FFFFFF',
    border: '1px solid #333333',
    borderRadius: '0',
    fontSize: '14px',
    fontFamily: '"JetBrains Mono", monospace',
    cursor: 'pointer'
  },
  nav: {
    flex: 1,
    padding: '20px 0',
    overflowY: 'auto'
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 20px',
    color: '#9CA3AF',
    textDecoration: 'none',
    transition: 'all 0.2s ease',
    fontFamily: '"Inter", sans-serif'
  },
  navItemActive: {
    backgroundColor: '#27272a',
    color: '#FFFFFF',
    borderLeft: '3px solid #6366F1'
  },
  navIcon: {
    marginRight: '12px',
    fontSize: '18px'
  },
  navLabel: {
    fontSize: '14px',
    fontWeight: '500'
  },
  footer: {
    padding: '20px',
    borderTop: '1px solid #333333'
  },
  footerText: {
    margin: 0,
    fontSize: '12px',
    color: '#6B7280',
    textAlign: 'center'
  }
};

export default Sidebar;
