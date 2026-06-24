import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import PageHeader from '../components/PageHeader';
import { squadValues, recentForm } from '../data/analytics';

const CustomTooltip = ({ active, payload, label, suffix = '' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ backgroundColor: '#111', border: '1px solid #2a2a2a', borderRadius: 6, padding: '8px 12px' }}>
      <p style={{ fontSize: 12, color: '#888', marginBottom: 3 }}>{label}</p>
      <p style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{payload[0].value}{suffix}</p>
    </div>
  );
};

// Form badge color
function formColor(pct) {
  if (pct >= 70) return '#e5e5e5';
  if (pct >= 64) return '#aaa';
  return '#666';
}

export default function Teams() {
  return (
    <div>
      <PageHeader
        title="Teams"
        subtitle="Squad market values and recent competitive form across top international sides"
      />

      {/* Squad values */}
      <div style={{ marginBottom: 16 }}>
        <ChartCard
          title="Squad Market Value (€M) — Top 10 Nations"
          subtitle="Transfermarkt valuations reflect depth and quality of available talent"
        >
          <ResponsiveContainer width="100%" height={270}>
            <BarChart
              layout="vertical"
              data={squadValues}
              margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[0, 950]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
                tickFormatter={v => `€${v}M`}
              />
              <YAxis
                dataKey="nation"
                type="category"
                width={100}
                tick={{ fill: '#888', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix="M" />} cursor={{ fill: '#1f1f1f' }} />
              <Bar dataKey="value" radius={[0, 3, 3, 0]} maxBarSize={14}>
                {squadValues.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? '#e5e5e5' : i === 1 ? '#bbb' : i === 2 ? '#888' : '#3a3a3a'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Recent form chart */}
        <ChartCard
          title="Recent Form — Win % (Last 50 Matches)"
          subtitle="Argentina lead current form, underscoring their 2026 favouritism"
        >
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              layout="vertical"
              data={[...recentForm].sort((a, b) => b.winPct - a.winPct)}
              margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[55, 75]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
                tickFormatter={v => `${v}%`}
              />
              <YAxis
                dataKey="nation"
                type="category"
                width={90}
                interval={0}
                tick={{ fill: '#888', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix="%" />} cursor={{ fill: '#1f1f1f' }} />
              <Bar dataKey="winPct" radius={[0, 3, 3, 0]} maxBarSize={14}>
                {[...recentForm]
                  .sort((a, b) => b.winPct - a.winPct)
                  .map((d, i) => (
                    <Cell key={i} fill={formColor(d.winPct)} />
                  ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Form table */}
        <ChartCard
          title="Team Form & Value Summary"
          subtitle="Cross-reference squad investment against current form"
        >
          <div style={{ overflowY: 'auto', maxHeight: 280 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #222' }}>
                  {['Nation', 'Squad Value (€M)', 'Form Win %'].map(h => (
                    <th
                      key={h}
                      style={{
                        textAlign: 'left',
                        padding: '6px 8px',
                        fontSize: 11,
                        fontWeight: 600,
                        color: '#444',
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {squadValues.map((sv, i) => {
                  const form = recentForm.find(r => r.nation === sv.nation);
                  return (
                    <tr
                      key={sv.nation}
                      style={{ borderBottom: '1px solid #1a1a1a' }}
                      onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#141414')}
                      onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '9px 8px', color: i < 3 ? '#fff' : '#888' }}>
                        {sv.nation}
                      </td>
                      <td style={{ padding: '9px 8px', color: '#aaa', fontVariantNumeric: 'tabular-nums' }}>
                        €{sv.value.toLocaleString()}M
                      </td>
                      <td style={{ padding: '9px 8px' }}>
                        {form ? (
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '2px 8px',
                              borderRadius: 4,
                              backgroundColor: '#1f1f1f',
                              color: formColor(form.winPct),
                              fontWeight: 500,
                              fontSize: 11,
                            }}
                          >
                            {form.winPct}%
                          </span>
                        ) : (
                          <span style={{ color: '#333' }}>—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </div>
    </div>
  );
}
