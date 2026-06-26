export function Select({ label, value, onChange, options, getLabel = (o) => o, getValue = (o) => o }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] uppercase tracking-wider text-slate-light font-mono-data">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-ink-soft border hairline rounded-lg px-3 py-2 text-sm text-paper outline-none focus:border-brass/50 transition-colors cursor-pointer"
      >
        {options.map((opt) => (
          <option key={getValue(opt)} value={getValue(opt)}>
            {getLabel(opt)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function SegmentedControl({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[11px] uppercase tracking-wider text-slate-light font-mono-data">
        {label}
      </span>
      <div className="flex rounded-lg border hairline overflow-hidden">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`flex-1 px-3 py-2 text-sm transition-colors ${
              value === opt.value
                ? "bg-brass text-ink font-medium"
                : "bg-ink-soft text-slate-light hover:text-paper"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
