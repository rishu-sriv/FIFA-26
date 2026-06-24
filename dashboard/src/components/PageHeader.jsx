export default function PageHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <h1 style={{ fontSize: 26, fontWeight: 600, color: '#fff', marginBottom: 7 }}>{title}</h1>
      <p style={{ fontSize: 14, color: '#555' }}>{subtitle}</p>
    </div>
  );
}
