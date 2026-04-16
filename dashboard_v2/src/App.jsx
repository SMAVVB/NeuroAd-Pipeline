import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import TribePage from './pages/TribePage';
import MiroFishPage from './pages/MiroFishPage';
import ClipPage from './pages/ClipPage';
import ViNetPage from './pages/ViNetPage';

function App() {
  return (
    <Router>
      <div style={styles.appContainer}>
        <Sidebar />
        <div style={styles.mainContent}>
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/tribe" element={<TribePage />} />
            <Route path="/mirofish" element={<MiroFishPage />} />
            <Route path="/clip" element={<ClipPage />} />
            <Route path="/vinet" element={<ViNetPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

const styles = {
  appContainer: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden'
  },
  mainContent: {
    flex: 1,
    overflow: 'hidden'
  }
};

export default App;
