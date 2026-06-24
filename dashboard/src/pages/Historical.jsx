import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import PageHeader from '../components/PageHeader';
import { goalsPerDecade, historicalWinPct, wcTitles, hostNationPerf } from '../data/analytics';

const CustomTooltip = ({ active, payload, label, suffix = '' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ backgroundColor: '#111', border: '1px solid #2a2a2a', borderRadius: 6, padding: '8px 12px' }}>
      <p style={{ fontSize: 12, color: '#888', marginBottom: 3 }}>{label}</p>
      <p style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{payload[0].value}{suffix}</p>
    </div>
  );
};

export default function Historical() {
  return (
    <div>
      <PageHeader
        title="Historical Analysis"
        subtitle="Long-run trends across 150+ years of international football"
      />

      {/* Goals per decade — full width */}
      <div style={{ marginBottom: 16 }}>
        <ChartCard
          title="Goals Per Match — Decade Trend (1870s–2020s)"
          subtitle="High-scoring early era gives way to tactical, defensive modern football"
        >
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={goalsPerDecade} margin={{ top: 10, right: 24, left: -10, bottom: 0 }}>
              <CartesianGrid stroke="#1e1e1e" strokeDasharray="0" vertical={false} />
              <XAxis
                dataKey="decade"
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
              />
              <YAxis
                domain={[2, 6.2]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix=" goals/match" />} cursor={{ stroke: '#2e2e2e' }} />
              <ReferenceLine y={2.74} stroke="#333" strokeDasharray="4 4" label={{ value: 'Modern avg 2.74', fill: '#444', fontSize: 10, position: 'insideTopRight' }} />
              <Line
                type="monotone"
                dataKey="avg"
                stroke="#e5e5e5"
                strokeWidth={2}
                dot={{ r: 3, fill: '#e5e5e5', strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#fff' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 2 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* WC Titles */}
        <ChartCard
          title="World Cup Titles by Nation"
          subtitle="Brazil leads all time with 5 — most recently in 2002"
        >
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              layout="vertical"
              data={wcTitles}
              margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[0, 6]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
                allowDecimals={false}
              />
              <YAxis
                dataKey="nation"
                type="category"
                width={100}
                tick={{ fill: '#888', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix=" titles" />} cursor={{ fill: '#1f1f1f' }} />
              <Bar dataKey="titles" radius={[0, 3, 3, 0]} maxBarSize={14}>
                {wcTitles.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? '#e5e5e5' : i === 1 ? '#999' : i === 2 ? '#666' : '#333'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Host nation performance */}
        <ChartCard
          title="Host Nation Win % at World Cup"
          subtitle="Uruguay (1930) remain undefeated — Qatar (2022) won none"
        >
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              layout="vertical"
              data={[...hostNationPerf].sort((a, b) => b.winPct - a.winPct)}
              margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[0, 110]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
                tickFormatter={v => `${v}%`}
              />
              <YAxis
                dataKey="nation"
                type="category"
                width={100}
                tick={{ fill: '#888', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix="%" />} cursor={{ fill: '#1f1f1f' }} />
              <Bar dataKey="winPct" radius={[0, 3, 3, 0]} maxBarSize={11}>
                {[...hostNationPerf]
                  .sort((a, b) => b.winPct - a.winPct)
                  .map((d, i) => (
                    <Cell
                      key={i}
                      fill={d.winPct >= 80 ? '#e5e5e5' : d.winPct >= 60 ? '#888' : d.winPct >= 40 ? '#555' : '#2e2e2e'}
                    />
                  ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Historical win % */}
      <ChartCard
        title="Historical Win % — Top 10 Nations (All Time)"
        subtitle="Brazil's dominance is clear — over 63% of all international matches won"
      >
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            layout="vertical"
            data={historicalWinPct}
            margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
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
              width={120}
              tick={{ fill: '#888', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip suffix="%" />} cursor={{ fill: '#1f1f1f' }} />
            <Bar dataKey="pct" radius={[0, 3, 3, 0]} maxBarSize={12}>
              {historicalWinPct.map((_, i) => (
                <Cell key={i} fill={i === 0 ? '#e5e5e5' : i < 3 ? '#888' : '#333'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
