import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

const FALLBACK = [
  { ticker: "RELIANCE", value: 0.0 },
  { ticker: "TCS", value: 0.0 },
  { ticker: "HDFCBANK", value: 0.0 },
];

export default function TickerTape() {
  const [items, setItems] = useState(FALLBACK);
  const [doubled, setDoubled] = useState([...FALLBACK, ...FALLBACK]);
  const [asOf, setAsOf] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/dashboard/latest-snapshot`)
      .then((r) => r.json())
      .then((d) => {
        const mapped = d.data
          .map((row) => ({
            ticker: row.Ticker.replace(".NS", ""),
            value: row.Daily_Return,
          }))
          .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
          .slice(0, 20);
        setItems(mapped);
        setAsOf(d.as_of);
      })
      .catch(() => {
        // keep fallback silently — no error shown to user
      });
  }, []);

  useEffect(() => {
    setDoubled([...items, ...items]);
  }, [items]);

  return (
    <div className="relative w-full overflow-hidden border-b hairline bg-ink-soft/60 py-2.5">
      <div className="flex w-max ticker-track">
        {doubled.map((item, i) => {
          const positive = item.value >= 0;
          return (
            <div
              key={`${item.ticker}-${i}`}
              className="flex items-center gap-2 px-6 font-mono-data text-[13px] whitespace-nowrap"
            >
              <span className="text-slate-light uppercase tracking-wider">
                {item.ticker}
              </span>
              <span
                className={positive ? "text-market-green-bright" : "text-brick-red-bright"}
              >
                {positive ? "▲" : "▼"} {Math.abs(item.value * 100).toFixed(2)}%
              </span>
              <span className="text-hairline">·</span>
            </div>
          );
        })}
      </div>

      {asOf && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden md:block">
          <span className="text-[10px] font-mono-data text-slate-light/60 bg-ink-soft px-2 py-0.5 rounded-full border hairline">
            As of {asOf}
          </span>
        </div>
      )}
    </div>
  );
}