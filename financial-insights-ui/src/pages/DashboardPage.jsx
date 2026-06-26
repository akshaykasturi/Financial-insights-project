import { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { Select, SegmentedControl } from "../components/Controls";
import { API_BASE } from "../lib/api";

const METRIC_OPTIONS = [
  { value: "avg_daily_return", label: "Avg Daily Return" },
  { value: "avg_volatility", label: "Volatility" },
  { value: "avg_pe_ratio", label: "P/E Ratio" },
];

const COLORS = {
  positive: "#2E9970",
  negative: "#C23E3E",
  neutral: "#C9A961",
};

function StatCard({ label, value, sub }) {
  return (
    <div className="rounded-xl border hairline bg-ink-card px-5 py-4">
      <p className="text-[11px] uppercase tracking-wider text-slate-light font-mono-data mb-1.5">
        {label}
      </p>
      <p className="font-display text-2xl text-paper">{value}</p>
      {sub && <p className="text-xs text-slate-light mt-1">{sub}</p>}
    </div>
  );
}

function ChartCard({ title, children, loading, empty }) {
  return (
    <div className="rounded-xl border hairline bg-ink-card p-5 md:p-6">
      <h3 className="font-display text-lg text-paper mb-4">{title}</h3>
      {loading ? (
        <div className="h-72 flex items-center justify-center text-slate-light text-sm">
          Loading data…
        </div>
      ) : empty ? (
        <div className="h-72 flex items-center justify-center text-slate-light text-sm">
          No data available for this selection.
        </div>
      ) : (
        children
      )}
    </div>
  );
}

const tooltipStyle = {
  contentStyle: {
    background: "#1C2429",
    border: "1px solid rgba(201, 169, 97, 0.25)",
    borderRadius: 8,
    fontSize: 13,
    color: "#F7F4ED",
  },
  labelStyle: { color: "#C9A961" },
};

export default function DashboardPage() {
  const [meta, setMeta] = useState(null);
  const [overview, setOverview] = useState(null);

  const [sectorYear, setSectorYear] = useState(null);
  const [sectorMetric, setSectorMetric] = useState("avg_daily_return");
  const [sectorData, setSectorData] = useState(null);
  const [sectorLoading, setSectorLoading] = useState(false);

  const [perfYear, setPerfYear] = useState(null);
  const [perfDirection, setPerfDirection] = useState("best");
  const [perfData, setPerfData] = useState(null);
  const [perfLoading, setPerfLoading] = useState(false);

  const [trendTicker, setTrendTicker] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [trendLoading, setTrendLoading] = useState(false);

  // Load meta + overview once
  useEffect(() => {
    fetch(`${API_BASE}/dashboard/meta`)
      .then((r) => r.json())
      .then((d) => {
        setMeta(d);
        const lastYear = d.years[d.years.length - 1];
        setSectorYear(lastYear);
        setPerfYear(lastYear);
        setTrendTicker(d.tickers[0]);
      })
      .catch(() => {});

    fetch(`${API_BASE}/dashboard/overview-stats`)
      .then((r) => r.json())
      .then(setOverview)
      .catch(() => {});
  }, []);

  // Sector comparison chart
  useEffect(() => {
    if (sectorYear == null) return;
    setSectorLoading(true);
    fetch(`${API_BASE}/dashboard/sector-comparison?year=${sectorYear}&metric=${sectorMetric}`)
      .then((r) => r.json())
      .then((d) => setSectorData(d.data))
      .catch(() => setSectorData([]))
      .finally(() => setSectorLoading(false));
  }, [sectorYear, sectorMetric]);

  // Top performers chart
  useEffect(() => {
    if (perfYear == null) return;
    setPerfLoading(true);
    fetch(`${API_BASE}/dashboard/top-performers?year=${perfYear}&top_n=10&direction=${perfDirection}`)
      .then((r) => r.json())
      .then((d) => setPerfData(d.data))
      .catch(() => setPerfData([]))
      .finally(() => setPerfLoading(false));
  }, [perfYear, perfDirection]);

  // Ticker trend chart
  useEffect(() => {
    if (!trendTicker) return;
    setTrendLoading(true);
    fetch(`${API_BASE}/dashboard/ticker-trend?ticker=${trendTicker}`)
      .then((r) => r.json())
      .then((d) => setTrendData(d.data))
      .catch(() => setTrendData([]))
      .finally(() => setTrendLoading(false));
  }, [trendTicker]);

  if (!meta) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-light">
        Loading market dashboard…
      </div>
    );
  }

  return (
    <div className="flex-1 px-4 md:px-10 py-8 max-w-6xl w-full mx-auto">
      <div className="mb-8">
        <h2 className="font-display text-3xl text-paper mb-1.5">Market Dashboard</h2>
        <p className="text-slate-light text-sm">
          Explore sector performance, top movers, and long-term trends across the Nifty 50.
        </p>
      </div>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          <StatCard label="Tracked Stocks" value={overview.total_tickers} />
          <StatCard label="Sectors" value={overview.total_sectors} />
          <StatCard
            label="Data Range"
            value={`${overview.year_range[0]}–${overview.year_range[1]}`}
          />
          <StatCard
            label="Records Analyzed"
            value={overview.total_records.toLocaleString()}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Sector Comparison */}
        <ChartCard title="Sector Comparison" loading={sectorLoading} empty={sectorData?.length === 0}>
          <div className="flex flex-wrap gap-4 mb-5">
            <div className="w-32">
              <Select
                label="Year"
                value={sectorYear}
                onChange={(v) => setSectorYear(Number(v))}
                options={meta.years}
              />
            </div>
            <div className="flex-1 min-w-[180px]">
              <SegmentedControl
                label="Metric"
                value={sectorMetric}
                onChange={setSectorMetric}
                options={METRIC_OPTIONS}
              />
            </div>
          </div>
          {sectorData && sectorData.length > 0 && (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={sectorData} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(201,169,97,0.08)" vertical={false} />
                <XAxis dataKey="sector" tick={{ fill: "#8A969C", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#8A969C", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {sectorData.map((entry, i) => (
                    <Cell key={i} fill={entry.value >= 0 ? COLORS.positive : COLORS.negative} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Top Performers */}
        <ChartCard title="Top Performers" loading={perfLoading} empty={perfData?.length === 0}>
          <div className="flex flex-wrap gap-4 mb-5">
            <div className="w-32">
              <Select
                label="Year"
                value={perfYear}
                onChange={(v) => setPerfYear(Number(v))}
                options={meta.years}
              />
            </div>
            <div className="flex-1 min-w-[160px]">
              <SegmentedControl
                label="Direction"
                value={perfDirection}
                onChange={setPerfDirection}
                options={[
                  { value: "best", label: "Best" },
                  { value: "worst", label: "Worst" },
                ]}
              />
            </div>
          </div>
          {perfData && perfData.length > 0 && (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={perfData} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(201,169,97,0.08)" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#8A969C", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="ticker"
                  tick={{ fill: "#8A969C", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={90}
                />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="yearly_return" radius={[0, 4, 4, 0]}>
                  {perfData.map((entry, i) => (
                    <Cell key={i} fill={entry.yearly_return >= 0 ? COLORS.positive : COLORS.negative} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Ticker Trend — full width */}
        <div className="lg:col-span-2">
          <ChartCard title="Stock Trend Over Time" loading={trendLoading} empty={trendData?.length === 0}>
            <div className="mb-5 w-48">
              <Select
                label="Ticker"
                value={trendTicker}
                onChange={setTrendTicker}
                options={meta.tickers}
              />
            </div>
            {trendData && trendData.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(201,169,97,0.08)" vertical={false} />
                  <XAxis dataKey="year" tick={{ fill: "#8A969C", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#8A969C", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Line
                    type="monotone"
                    dataKey="avg_close"
                    stroke="#C9A961"
                    strokeWidth={2}
                    dot={{ fill: "#C9A961", r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      </div>
    </div>
  );
}
