"use client";

import { useEffect, useState } from "react";

type Point = { date: string; predicted_price: number };
type ModelForecastComparison = { model: string; forecast: Point[]; error?: string };
type Forecast = {
  model: string; horizon_months: number; last_observation_date: string;
  last_observed_price: number; data_age_days: number; is_stale: boolean;
  forecast: Point[]; forecast_comparison: ModelForecastComparison[]; limitations: string[];
};
type History = { date: string; avg_monthly_price: number };
type Evaluation = { selected_model: string; selection_metric: string; windows_evaluated: number; results: { model: string; mean_mae: number; mean_rmse: number; mean_mape_percent: number }[]; warning: string };

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const money = (v: number) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(v);
const panel: React.CSSProperties = {
  background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16,
  padding: 20, boxShadow: "0 4px 18px rgba(15,23,42,0.04)", minWidth: 0
};
const th: React.CSSProperties = {
  textAlign: "left", padding: "11px 10px", color: "#64748b", fontSize: 12,
  textTransform: "uppercase", letterSpacing: ".04em", background: "#f8fafc"
};
const td: React.CSSProperties = { padding: "11px 10px", borderTop: "1px solid #eef2f7", fontSize: 14 };

export default function Home() {
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [history, setHistory] = useState<History[]>([]);
  const [horizon, setHorizon] = useState(12);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [training, setTraining] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [trainingMessage, setTrainingMessage] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const [f, h] = await Promise.all([
        fetch(`${API}/forecast?horizon=${horizon}`),
        fetch(`${API}/history?limit=${horizon}`)
      ]);
      if (!f.ok) throw new Error(`Forecast API failed (${f.status}): ${await f.text()}`);
      if (!h.ok) throw new Error(`History API failed (${h.status})`);
      setForecast(await f.json());
      setHistory(await h.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to connect to the API.");
    } finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [horizon]);

  async function uploadCsv(file?: File) {
    if (!file) return;
    setUploading(true); setUploadMessage(""); setError("");
    try {
      const response = await fetch(`${API}/dataset`, {
        method: "POST",
        headers: { "Content-Type": "text/csv" },
        body: await file.text(),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `Upload failed (${response.status})`);
      setUploadMessage(`Dataset updated: ${result.observations} monthly records, ${result.first_observation_date} to ${result.last_observation_date}.`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to upload the CSV.");
    } finally { setUploading(false); }
  }

  async function trainEvaluate() {
    setTraining(true); setTrainingMessage(""); setError("");
    try {
      const response = await fetch(`${API}/train-evaluate?windows=4&horizon=12`, { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `Model evaluation failed (${response.status})`);
      setEvaluation(result);
      setTrainingMessage(`Evaluation complete. Selected ${result.selected_model} by mean MAE across ${result.windows_evaluated} rolling-origin windows.`);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to evaluate models."); }
    finally { setTraining(false); }
  }

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "30px 20px 48px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 18, flexWrap: "wrap", marginBottom: 24 }}>
        <div>
          <div style={{ color: "#2563eb", fontWeight: 800, fontSize: 12, letterSpacing: ".12em", marginBottom: 8 }}>WAY2AGRIBUSINESS · PRICE INTELLIGENCE</div>
          <h1 style={{ margin: "0 0 8px", fontSize: "clamp(27px,4vw,38px)", letterSpacing: "-.04em", color: "#0f172a" }}>Monthly Price Forecast</h1>
          <p style={{ color: "#64748b", margin: 0, maxWidth: 680, lineHeight: 1.6 }}>Review the latest observed prices alongside the selected forecast horizon.</p>
        </div>
        <div style={{ ...panel, padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
          <label htmlFor="horizon" style={{ fontWeight: 700, fontSize: 13, whiteSpace: "nowrap" }}>Forecast horizon</label>
          <select id="horizon" value={horizon} onChange={e => setHorizon(Number(e.target.value))}
            style={{ border: "1px solid #cbd5e1", borderRadius: 9, padding: "10px 12px", fontWeight: 700, background: "#fff", color: "#0f172a" }}>
            <option value={6}>6 months</option><option value={12}>12 months</option><option value={18}>18 months</option><option value={24}>24 months</option>
          </select>
        </div>
      </header>

      <section style={{ ...panel, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap", marginBottom: 18 }}>
        <div><h2 style={{ margin: "0 0 5px", fontSize: 17, color: "#0f172a" }}>Update price data</h2><p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Upload a CSV with <code>date</code> and <code>avg_monthly_price</code> columns; one record per month, at least 24 months.</p></div>
        <label style={{ display: "inline-flex", alignItems: "center", gap: 8, background: uploading ? "#94a3b8" : "#1d4ed8", color: "white", borderRadius: 10, padding: "11px 15px", fontWeight: 700, fontSize: 13, cursor: uploading ? "wait" : "pointer", whiteSpace: "nowrap" }}>
          {uploading ? "Uploading…" : "Upload CSV"}
          <input type="file" accept=".csv,text/csv" disabled={uploading} onChange={e => { const file = e.target.files?.[0]; void uploadCsv(file); e.currentTarget.value = ""; }} style={{ display: "none" }} />
        </label>
        {uploadMessage && <p role="status" style={{ flexBasis: "100%", margin: 0, color: "#166534", fontSize: 13 }}>{uploadMessage}</p>}
      </section>

      <section style={{ ...panel, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap", marginBottom: 18 }}>
        <div><h2 style={{ margin: "0 0 5px", fontSize: 17, color: "#0f172a" }}>Train and compare models</h2><p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Compare four forecasting candidates using four chronological 12-month validation windows. Selection prioritizes mean MAE.</p></div>
        <button type="button" onClick={trainEvaluate} disabled={training} style={{ border: 0, background: training ? "#94a3b8" : "#0f766e", color: "white", borderRadius: 10, padding: "11px 15px", fontWeight: 700, fontSize: 13, cursor: training ? "wait" : "pointer" }}>{training ? "Evaluating models…" : "Run model evaluation"}</button>
        {trainingMessage && <p role="status" style={{ flexBasis: "100%", margin: 0, color: "#166534", fontSize: 13 }}>{trainingMessage}</p>}
      </section>
      {evaluation && <section style={{ ...panel, marginBottom: 18 }}>
        <h2 style={{ margin: "0 0 6px", fontSize: 18, color: "#0f172a" }}>Rolling-origin evaluation results</h2>
        <p style={{ margin: "0 0 12px", color: "#64748b", fontSize: 13 }}>Selected model: <strong>{evaluation.selected_model}</strong>. Lower is better for all listed metrics.</p>
        <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}><thead><tr><th style={th}>Model</th><th style={{ ...th, textAlign: "right" }}>Mean MAE</th><th style={{ ...th, textAlign: "right" }}>Mean RMSE</th><th style={{ ...th, textAlign: "right" }}>Mean MAPE</th></tr></thead><tbody>{evaluation.results.map(row => <tr key={row.model} style={row.model === evaluation.selected_model ? { background: "#f0fdf4" } : undefined}><td style={td}>{row.model}{row.model === evaluation.selected_model ? " · selected" : ""}</td><td style={{ ...td, textAlign: "right" }}>{money(row.mean_mae)}</td><td style={{ ...td, textAlign: "right" }}>{money(row.mean_rmse)}</td><td style={{ ...td, textAlign: "right" }}>{row.mean_mape_percent.toFixed(2)}%</td></tr>)}</tbody></table></div>
        <p style={{ margin: "12px 0 0", color: "#92400e", fontSize: 12 }}>{evaluation.warning}</p>
      </section>}
      {error && <div role="alert" style={{ ...panel, borderColor: "#fca5a5", color: "#991b1b", marginBottom: 18 }}>{error}<p>Confirm FastAPI is running at {API}.</p></div>}

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))", gap: 14, marginBottom: 18 }}>
        <div style={panel}><div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em" }}>Last observation</div><div style={{ fontSize: 29, fontWeight: 800, margin: "10px 0 5px", color: "#0f172a" }}>{forecast ? money(forecast.last_observed_price) : "—"}</div><div style={{ color: "#64748b", fontSize: 13 }}>Observed {forecast?.last_observation_date ?? "—"}</div></div>
        <div style={panel}><div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em" }}>Forecasting method</div><div style={{ fontSize: 21, fontWeight: 800, margin: "12px 0 7px", color: "#0f172a" }}>{forecast?.model ?? "—"}</div><div style={{ color: "#64748b", fontSize: 13 }}>Horizon: {horizon} months</div></div>
        <div style={panel}><div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em" }}>Data freshness</div><div style={{ fontSize: 21, fontWeight: 800, margin: "12px 0 7px", color: forecast?.is_stale ? "#b45309" : "#15803d" }}>{forecast ? (forecast.is_stale ? "Stale data" : "Recent data") : "—"}</div><div style={{ color: "#64748b", fontSize: 13 }}>{forecast ? `${forecast.data_age_days} days since last observation` : "Checking data…"}</div></div>
      </section>

      {forecast?.is_stale && <div style={{ ...panel, background: "#fffbeb", borderColor: "#fcd34d", marginBottom: 18, color: "#92400e" }}><strong>Data needs refreshing.</strong> The supplied dataset ends on {forecast.last_observation_date}. Forecast values are a baseline illustration, not current market guidance.</div>}

      {forecast?.forecast_comparison && <section style={{ ...panel, marginTop: 18, marginBottom: 18 }}>
        <div style={{ marginBottom: 14 }}>
          <h2 style={{ margin: "0 0 5px", fontSize: 20, color: "#0f172a" }}>Compare forecast values across all models</h2>
          <p style={{ margin: 0, color: "#64748b", fontSize: 13, lineHeight: 1.6 }}>
            This table shows each model's own prediction for the same month. The Naive baseline repeats the last observed price by design; Drift, Holt damped trend, and Holt-Winters can produce different values. Values are model estimates, not live market prices.
          </p>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
            <thead><tr>
              <th style={th}>Forecast month</th>
              {forecast.forecast_comparison.map(m => <th key={m.model} style={{ ...th, textAlign: "right" }}>{m.model}</th>)}
            </tr></thead>
            <tbody>
              {(forecast.forecast_comparison.find(m => m.forecast.length > 0)?.forecast ?? []).map((point, i) => (
                <tr key={point.date}>
                  <td style={td}>{new Date(point.date + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "numeric" })}</td>
                  {forecast.forecast_comparison.map(m => <td key={m.model} style={{ ...td, textAlign: "right", fontWeight: m.model === forecast.model ? 800 : 500 }}>
                    {m.forecast[i] ? money(m.forecast[i].predicted_price) : (m.error ? "Unavailable" : "—")}
                  </td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {forecast.forecast_comparison.some(m => m.error) && <p style={{ color: "#b45309", fontSize: 12, marginBottom: 0 }}>
          One or more models could not be fitted for this dataset. Check the API response for each model's error.
        </p>}
      </section>}

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(min(100%,430px),1fr))", gap: 18, alignItems: "start" }}>
        <div style={panel}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 16 }}>
            <div><h2 style={{ margin: "0 0 5px", fontSize: 20, color: "#0f172a" }}>Price forecast</h2><p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Next {horizon} months · {forecast?.model ?? "Loading"}</p></div>
            <span style={{ background: "#eff6ff", color: "#1d4ed8", borderRadius: 999, padding: "6px 10px", fontSize: 12, fontWeight: 800 }}>{horizon}M</span>
          </div>
          {loading && !forecast ? <p>Loading forecast…</p> : <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><th style={th}>Forecast month</th><th style={{ ...th, textAlign: "right" }}>Predicted price</th></tr></thead>
            <tbody>{(forecast?.forecast ?? []).map(p => <tr key={p.date}><td style={td}>{new Date(p.date + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "numeric" })}</td><td style={{ ...td, textAlign: "right", fontWeight: 700 }}>{money(p.predicted_price)}</td></tr>)}</tbody>
          </table></div>}
          <p style={{ color: "#94a3b8", fontSize: 12, margin: "14px 0 0" }}>This panel shows the selected model. Use the comparison table below to inspect values from every candidate model side by side.</p>
        </div>

        <div style={panel}>
          <div style={{ marginBottom: 16 }}><h2 style={{ margin: "0 0 5px", fontSize: 20, color: "#0f172a" }}>Recent price history</h2><p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Latest {horizon} observed months</p></div>
          {history.length === 0 ? <p>No history loaded yet.</p> : <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><th style={th}>Observed month</th><th style={{ ...th, textAlign: "right" }}>Average price</th></tr></thead>
            <tbody>{history.map(x => <tr key={x.date}><td style={td}>{new Date(x.date + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "numeric" })}</td><td style={{ ...td, textAlign: "right", fontWeight: 700 }}>{money(x.avg_monthly_price)}</td></tr>)}</tbody>
          </table></div>}
        </div>
      </section>

      <section style={{ ...panel, marginTop: 18 }}>
        <h2 style={{ margin: "0 0 10px", fontSize: 18 }}>How to interpret this dashboard</h2>
        <ul style={{ color: "#475569", lineHeight: 1.8, paddingLeft: 20, margin: 0 }}>
          {(forecast?.limitations ?? ["Forecasts are decision support only."]).map(x => <li key={x}>{x}</li>)}
        </ul>
        <p style={{ color: "#94a3b8", fontSize: 12, marginBottom: 0 }}>The dataset does not identify the commodity, market, or unit; values are displayed without assuming a currency.</p>
      </section>
      <footer style={{ color: "#94a3b8", fontSize: 12, textAlign: "center", marginTop: 24 }}>Way2Agribusiness · Forecasting prototype · Validate current data before operational use</footer>
    </main>
  );
}
