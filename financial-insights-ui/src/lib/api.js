const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function post(path, body, timeoutMs = 90000) {
  const adminKey = localStorage.getItem("admin_key");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json",
        ...(adminKey ? { "X-Admin-Key": adminKey } : {})
       },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Request failed (${res.status}): ${text}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timeout);
    if (err.name === "AbortError") {
      throw new Error("The request took too long. The server may be waking up — please try again in a moment.");
    }
    throw err;
  }
}

async function get(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return await res.json();
}

export const api = {
  chat: (question, sessionId) =>
    post("/chat", { question, session_id: sessionId }),

  runPipeline: (task) =>
    post("/pipeline/run", { task }, 180000),

  runIngestion: (task) =>
    post("/agents/ingestion", { task }),

  runProcessing: (task) =>
    post("/agents/processing", { task }),

  runAnalytics: (task) =>
    post("/agents/analytics", { task }),

  recentLogs: (limit = 15) =>
    get(`/logs/recent?limit=${limit}`),

  tokenUsage: () =>
    get("/logs/usage"),
};

export { API_BASE };
