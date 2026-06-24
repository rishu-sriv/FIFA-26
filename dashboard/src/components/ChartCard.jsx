export default function ChartCard({ title, subtitle, children, style }) {
  return (
    <div
      style={{
        backgroundColor: '#1a1a1a',
        border: '1px solid #222',
        borderRadius: 8,
        padding: '20px 24px',
        ...style,
      }}
    >
      <p style={{ fontSize: 14, fontWeight: 600, color: '#fff', marginBottom: 5 }}>{title}</p>
      {subtitle && (
        <p style={{ fontSize: 12, color: '#555', marginBottom: 20 }}>{subtitle}</p>
      )}
      {children}
    </div>
  );
}
