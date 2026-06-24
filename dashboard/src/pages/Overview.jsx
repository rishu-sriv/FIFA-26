import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, LineChart, Line, CartesianGrid,
} from 'recharts';
import KpiCard from '../components/KpiCard';
import ChartCard from '../components/ChartCard';
import PageHeader from '../components/PageHeader';
import { kpiCards, historicalWinPct, goalsPerDecade, venueStats } from '../data/analytics';

const CHART_COLORS = {
  default: '#3a3a3a',
  accent: '#e5e5e5',
  muted: '#2a2a2a',
};

const CustomTooltip = ({ active, payload, label, suffix = '' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ backgroundColor: '#111', border: '1px solid #2a2a2a', borderRadius: 6, padding: '8px 12px' }}>
      <p style={{ fontSize: 12, color: '#888', marginBottom: 3 }}>{label}</p>
      <p style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{payload[0].value}{suffix}</p>
    </div>
  );
};

export default function Overview() {
  return (
    <div>
      <PageHeader
        title="Overview"
        subtitle="High-level summary of international football data from 1872 to 2026"
      />

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        {kpiCards.map(c => (
          <KpiCard key={c.label} label={c.label} value={c.value} />
        ))}
      </div>

      {/* Charts row 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>

        {/* Win % bar chart */}
        <ChartCard
          title="Top 10 Nations by Win Rate"
          subtitle="All international matches — win percentage across history"
        >
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              layout="vertical"
              data={historicalWinPct}
              margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[45, 68]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
                tickFormatter={v => `${v}%`}
              />
              <YAxis
                dataKey="nation"
                type="category"
                width={110}
                tick={{ fill: '#888', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix="%" />} cursor={{ fill: '#1f1f1f' }} />
              <Bar dataKey="pct" radius={[0, 3, 3, 0]} maxBarSize={14}>
                {historicalWinPct.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? '#e5e5e5' : i === 1 ? '#aaa' : '#3a3a3a'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Goals per decade line */}
        <ChartCard
          title="Average Goals Per Match by Decade"
          subtitle="Scoring trends from 1870s to 2020s — modern game is more tactical"
        >
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={goalsPerDecade} margin={{ top: 6, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid stroke="#1e1e1e" strokeDasharray="0" vertical={false} />
              <XAxis
                dataKey="decade"
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
              />
              <YAxis
                domain={[2, 6]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#333' }} />
              <Line
                type="monotone"
                dataKey="avg"
                stroke="#e5e5e5"
                strokeWidth={1.5}
                dot={{ r: 2.5, fill: '#e5e5e5', strokeWidth: 0 }}
                activeDot={{ r: 4, fill: '#fff' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Venue comparison */}
      <ChartCard
        title="Home vs Neutral Venue Win Rate"
        subtitle="Home advantage is measurable — teams win significantly more on home soil"
      >
        <div style={{ display: 'flex', gap: 16, alignItems: 'stretch' }}>
          {venueStats.map((v, i) => (
            <div
              key={v.venue}
              style={{
                flex: 1,
                backgroundColor: '#141414',
                border: `1px solid ${i === 0 ? '#3a3a3a' : '#222'}`,
                borderRadius: 6,
                padding: '24px 28px',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
            >
              <p style={{ fontSize: 12, color: '#555', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{v.venue}</p>
              <p style={{ fontSize: 44, fontWeight: 700, color: i === 0 ? '#fff' : '#666', lineHeight: 1 }}>
                {v.winRate}%
              </p>
              <p style={{ fontSize: 11, color: '#444' }}>Win Rate</p>
              {/* Bar fill */}
              <div style={{ marginTop: 8, height: 4, backgroundColor: '#222', borderRadius: 2 }}>
                <div
                  style={{
                    height: '100%',
                    width: `${v.winRate}%`,
                    backgroundColor: i === 0 ? '#e5e5e5' : '#3a3a3a',
                    borderRadius: 2,
                  }}
                />
              </div>
            </div>
          ))}
          <div style={{ flex: 2, display: 'flex', alignItems: 'center', padding: '0 8px' }}>
            <div>
              <p style={{ fontSize: 14, fontWeight: 500, color: '#aaa', marginBottom: 10 }}>
                +6.5 percentage point advantage
              </p>
              <p style={{ fontSize: 13, color: '#444', lineHeight: 1.7 }}>
                Across 49,477 international matches, teams playing at home win 50.7% of the time compared to 44.2% on neutral ground — a consistent and statistically significant edge driven by crowd support, familiar conditions, and reduced travel fatigue.
              </p>
            </div>
          </div>
        </div>
      </ChartCard>
    </div>
  );
}
