import { LayoutDashboard, TrendingUp, Users, Trophy } from 'lucide-react';

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'historical', label: 'Historical', icon: TrendingUp },
  { id: 'teams', label: 'Teams', icon: Users },
  { id: 'predictions', label: '2026 Predictions', icon: Trophy },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside
      style={{ width: 220, minWidth: 220, backgroundColor: '#0f0f0f', borderRight: '1px solid #1f1f1f' }}
      className="fixed top-0 left-0 h-screen flex flex-col z-50"
    >
      {/* Logo / Brand */}
      <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid #1f1f1f' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              backgroundColor: '#ffffff',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Trophy size={16} color="#0f0f0f" />
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#ffffff', lineHeight: 1.2 }}>FIFA Analytics</p>
            <p style={{ fontSize: 11, color: '#555', lineHeight: 1.2 }}>WC 2026</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: '12px 0', flex: 1 }}>
        <p style={{ fontSize: 10, fontWeight: 600, color: '#444', letterSpacing: '0.08em', textTransform: 'uppercase', padding: '8px 20px 6px' }}>
          Navigation
        </p>
        {navItems.map(({ id, label, icon: Icon }) => {
          const active = activePage === id;
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '9px 20px',
                background: active ? '#1a1a1a' : 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: active ? '#ffffff' : '#666',
                fontSize: 14,
                fontWeight: active ? 500 : 400,
                fontFamily: 'inherit',
                textAlign: 'left',
                borderLeft: active ? '2px solid #ffffff' : '2px solid transparent',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { if (!active) { e.currentTarget.style.color = '#aaa'; e.currentTarget.style.background = '#141414'; } }}
              onMouseLeave={e => { if (!active) { e.currentTarget.style.color = '#666'; e.currentTarget.style.background = 'transparent'; } }}
            >
              <Icon size={15} />
              {label}
            </button>
          );
        })}
      </nav>

      {/* Footer tag */}
      <div style={{ padding: '16px 20px 20px', borderTop: '1px solid #1f1f1f' }}>
        <p style={{ fontSize: 10, color: '#2e2e2e', lineHeight: 1.5, marginBottom: 14 }}>
          Powered by XGBoost<br />& Monte Carlo
        </p>
        <div style={{ borderTop: '1px solid #1a1a1a', paddingTop: 14 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#aaa', letterSpacing: '0.04em', marginBottom: 3 }}>
            SAMEER
          </p>
          <p style={{ fontSize: 10, color: '#444', letterSpacing: '0.06em', lineHeight: 1.5 }}>
            FRIENDLY NEIGHBOURHOOD<br />DEVELOPER
          </p>
        </div>
      </div>
    </aside>
  );
}
