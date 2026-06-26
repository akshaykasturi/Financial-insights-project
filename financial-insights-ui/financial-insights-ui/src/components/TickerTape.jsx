import { useEffect, useState } from "react";

// Signature element: a scrolling ticker tape using real sector data.
// Falls back to a static set if the API isn't reachable yet.
const FALLBACK = [
  { sector: "IT", value: 0.08 },
  { sector: "Financials", value: -0.01 },
  { sector: "Pharma", value: 0.13 },
  { sector: "Energy", value: 0.08 },
  { sector: "Automobile", value: 0.21 },
  { sector: "Metals", value: 0.19 },
];

export default function TickerTape({ items = FALLBACK }) {
  const [doubled, setDoubled] = useState([...items, ...items]);

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
              key={`${item.sector}-${i}`}
              className="flex items-center gap-2 px-6 font-mono-data text-[13px] whitespace-nowrap"
            >
              <span className="text-slate-light uppercase tracking-wider">
                {item.sector}
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
    </div>
  );
}
