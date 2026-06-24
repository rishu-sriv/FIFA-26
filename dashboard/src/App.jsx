import { useState } from 'react';
import './index.css';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import Historical from './pages/Historical';
import Teams from './pages/Teams';
import Predictions from './pages/Predictions';

const PAGES = {
  overview: Overview,
  historical: Historical,
  teams: Teams,
  predictions: Predictions,
};

export default function App() {
  const [activePage, setActivePage] = useState('overview');
  const PageComponent = PAGES[activePage];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      {/* Main content */}
      <div style={{ marginLeft: 220, flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <main style={{ flex: 1, padding: '32px 36px 24px' }}>
          <PageComponent />
        </main>

        {/* Footer */}
        <footer
          style={{
            borderTop: '1px solid #1a1a1a',
            padding: '14px 36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <p style={{ fontSize: 12, color: '#2e2e2e', letterSpacing: '0.02em' }}>
            FIFA World Cup 2026 Analytics Platform&nbsp;&nbsp;|&nbsp;&nbsp;Built with Python, PostgreSQL, XGBoost &amp; React
          </p>
        </footer>
      </div>
    </div>
  );
}
