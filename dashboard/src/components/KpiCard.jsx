export default function KpiCard({ label, value }) {
  return (
    <div
      style={{
        backgroundColor: '#1a1a1a',
        border: '1px solid #222',
        borderRadius: 8,
        padding: '20px 24px',
        transition: 'border-color 0.15s',
        cursor: 'default',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = '#333')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = '#222')}
    >
      <p style={{ fontSize: 12, fontWeight: 500, color: '#555', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>
        {label}
      </p>
      <p style={{ fontSize: 32, fontWeight: 600, color: '#fff', lineHeight: 1 }}>
        {value}
      </p>
    </div>
  );
}
