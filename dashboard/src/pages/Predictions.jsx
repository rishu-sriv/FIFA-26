import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import PageHeader from '../components/PageHeader';
import { predictions2026 } from '../data/analytics';

const CustomTooltip = ({ active, payload, label, suffix = '' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ backgroundColor: '#111', border: '1px solid #2a2a2a', borderRadius: 6, padding: '8px 12px' }}>
      <p style={{ fontSize: 12, color: '#888', marginBottom: 3 }}>{label}</p>
      <p style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{payload[0].value}{suffix}</p>
    </div>
  );
};

function barFill(i) {
  if (i === 0) return '#e5e5e5';
  if (i === 1) return '#aaa';
  if (i === 2) return '#777';
  return '#2e2e2e';
}

const finalData = predictions2026.filter(d => d.finalProb !== null);

export default function Predictions() {
  return (
    <div>
      <PageHeader
        title="2026 World Cup Predictions"
        subtitle="Monte Carlo simulation (10,000 runs) + XGBoost model — win probabilities for FIFA World Cup 2026"
      />

      {/* Top 3 spotlight */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 28 }}>
        {predictions2026.slice(0, 3).map((d, i) => (
          <div
            key={d.nation}
            style={{
              backgroundColor: '#1a1a1a',
              border: `1px solid ${i === 0 ? '#3a3a3a' : '#222'}`,
              borderRadius: 8,
              padding: '24px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <p style={{ fontSize: 12, color: '#555', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                {i === 0 ? 'Top Favourite' : i === 1 ? '2nd Favourite' : '3rd Favourite'}
              </p>
              <span
                style={{
                  fontSize: 10,
                  padding: '2px 7px',
                  borderRadius: 3,
                  backgroundColor: '#111',
                  color: '#444',
                  border: '1px solid #222',
                }}
              >
                #{i + 1}
              </span>
            </div>
            <p style={{ fontSize: 26, fontWeight: 700, color: i === 0 ? '#fff' : '#aaa', marginBottom: 4 }}>
              {d.nation}
            </p>
            <p style={{ fontSize: 36, fontWeight: 700, color: i === 0 ? '#fff' : '#666', lineHeight: 1, marginBottom: 8 }}>
              {d.winProb}%
            </p>
            <p style={{ fontSize: 12, color: '#444' }}>Tournament win probability</p>
            {d.finalProb && (
              <p style={{ fontSize: 12, color: '#555', marginTop: 6 }}>
                Final reach: <span style={{ color: '#888' }}>{d.finalProb}%</span>
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Full predictions chart */}
      <div style={{ marginBottom: 16 }}>
        <ChartCard
          title="Tournament Winner Probabilities — All 15 Nations"
          subtitle="Model output: Argentina clear favourites, substantial drop-off after Spain and Brazil"
        >
          <ResponsiveContainer width="100%" height={390}>
            <BarChart
              layout="vertical"
              data={predictions2026}
              margin={{ top: 0, right: 40, left: 20, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[0, 26]}
                tick={{ fill: '#444', fontSize: 12 }}
                axisLine={{ stroke: '#222' }}
                tickLine={false}
                tickFormatter={v => `${v}%`}
              />
              <YAxis
                dataKey="nation"
                type="category"
                width={110}
                interval={0}
                tick={{ fill: '#888', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip suffix="%" />} cursor={{ fill: '#1f1f1f' }} />
              <Bar dataKey="winProb" radius={[0, 3, 3, 0]} maxBarSize={14}>
                {predictions2026.map((_, i) => (
                  <Cell key={i} fill={barFill(i)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Finals probability */}
      <ChartCard
        title="Probability of Reaching the Final — Top 8 Nations"
        subtitle="Stage probabilities from Monte Carlo simulation across 10,000 tournament runs"
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 4 }}>
          {finalData.map((d, i) => (
            <div
              key={d.nation}
              style={{
                backgroundColor: '#141414',
                border: '1px solid #1e1e1e',
                borderRadius: 6,
                padding: '16px',
              }}
            >
              <p style={{ fontSize: 11, fontWeight: 500, color: i < 2 ? '#bbb' : '#666', marginBottom: 6 }}>
                {d.nation}
              </p>
              <p style={{ fontSize: 22, fontWeight: 700, color: i < 2 ? '#fff' : '#555', marginBottom: 4 }}>
                {d.finalProb}%
              </p>
              <div style={{ height: 3, backgroundColor: '#222', borderRadius: 2 }}>
                <div
                  style={{
                    height: '100%',
                    width: `${(d.finalProb / 40) * 100}%`,
                    backgroundColor: i < 3 ? '#4a4a4a' : '#2a2a2a',
                    borderRadius: 2,
                  }}
                />
              </div>
              <p style={{ fontSize: 10, color: '#333', marginTop: 6 }}>Final reach</p>
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  );
}
