import { useState, useEffect } from "react";
import { Play, RefreshCw, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";




export default function AdminPage() {

  
const [authKey, setAuthKey] = useState(localStorage.getItem("admin_key") || "");
const [authed, setAuthed] = useState(!!authKey);

function handleLogin(key) {
  localStorage.setItem("admin_key", key);
  setAuthKey(key);
  setAuthed(true);
}

if (!authed) {
  return (
    <div className="flex-1 flex items-center justify-center px-4">
      <div className="max-w-sm w-full">
        <h2 className="font-display text-2xl text-paper mb-4">Admin Access</h2>
        <input
          type="password"
          placeholder="Enter admin key"
          onKeyDown={(e) => e.key === "Enter" && handleLogin(e.target.value)}
          className="w-full bg-ink-soft border hairline rounded-lg px-3 py-2.5 text-paper outline-none focus:border-brass/50"
        />
      </div>
    </div>
  );
}
  const [task, setTask] = useState(
    "Validate the data, analyze IT sector performance, and generate a 2024 insights report."
  );
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const [logs, setLogs] = useState([]);
  const [usage, setUsage] = useState(null);

  function loadLogs() {
    api.recentLogs(15).then((d) => setLogs(d.logs)).catch(() => {});
    api.tokenUsage().then(setUsage).catch(() => {});
  }

  useEffect(() => {
    loadLogs();
  }, []);

  async function runPipeline() {
    setRunning(true);
    setErrorMsg(null);
    setResult(null);
    try {
      const res = await api.runPipeline(task);
      setResult(res.result);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setRunning(false);
      loadLogs();
    }
  }

  return (
    <div className="flex-1 px-4 md:px-10 py-8 max-w-5xl w-full mx-auto">
      <div className="mb-8 flex items-center gap-3">
        <h2 className="font-display text-3xl text-paper">Admin Panel</h2>
        <span className="text-[11px] font-mono-data uppercase tracking-wider text-brick-red-bright border border-brick-red/30 rounded-full px-2.5 py-0.5">
          Internal Only
        </span>
      </div>

      <div className="rounded-xl border hairline bg-ink-card p-6 mb-8">
        <h3 className="font-display text-lg text-paper mb-1">Run Insights Pipeline</h3>
        <p className="text-sm text-slate-light mb-4">
          Triggers the Ingestion → Processing → Analytics agent chain. Takes 30–90 seconds.
        </p>

        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          rows={2}
          className="w-full bg-ink-soft border hairline rounded-lg px-3 py-2.5 text-sm text-paper outline-none focus:border-brass/50 transition-colors mb-4 resize-none"
        />

        <button
          onClick={runPipeline}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-brass text-ink font-medium text-sm hover:bg-brass-bright disabled:opacity-50 transition-colors"
        >
          {running ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {running ? "Running pipeline…" : "Run Pipeline"}
        </button>

        {errorMsg && (
          <div className="mt-4 flex items-start gap-2 text-sm text-brick-red-bright bg-brick-red/10 border border-brick-red/25 rounded-lg px-3 py-2.5">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {result && (
          <div className="mt-5 bg-ink-soft border hairline rounded-lg p-4 text-sm text-paper leading-relaxed whitespace-pre-wrap">
            {result}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border hairline bg-ink-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display text-lg text-paper">Recent Activity</h3>
            <button onClick={loadLogs} className="text-slate-light hover:text-brass transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {logs.map((log, i) => (
              <div key={i} className="border-b hairline pb-3 last:border-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={log.status === "success" ? "text-market-green-bright" : "text-brick-red-bright"}>
                    {log.status === "success" ? "●" : "○"}
                  </span>
                  <span className="font-medium text-sm text-paper">{log.agent_name}</span>
                </div>
                <p className="text-xs text-slate-light truncate">{log.message}</p>
                <p className="text-[11px] font-mono-data text-slate-light/60 mt-0.5">
                  {log.model} · ~{log.est_tokens} tok
                </p>
              </div>
            ))}
            {logs.length === 0 && (
              <p className="text-sm text-slate-light">No activity yet.</p>
            )}
          </div>
        </div>

        <div className="rounded-xl border hairline bg-ink-card p-6">
          <h3 className="font-display text-lg text-paper mb-4">Token Usage Today</h3>
          <div className="space-y-4">
            {usage &&
              Object.entries(usage).map(([model, stats]) => (
                <div key={model}>
                  <p className="text-xs font-mono-data text-slate-light mb-1">{model}</p>
                  <p className="font-display text-xl text-paper">
                    {stats.total_tokens_today.toLocaleString()}
                    <span className="text-sm text-slate-light ml-2">tokens</span>
                  </p>
                  <p className="text-xs text-market-green-bright">{stats.calls_today} calls today</p>
                </div>
              ))}
            {(!usage || Object.keys(usage).length === 0) && (
              <p className="text-sm text-slate-light">No usage recorded yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
