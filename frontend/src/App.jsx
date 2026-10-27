import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  Activity,
  BrainCircuit,
  ChevronRight,
  Database,
  Gauge,
  Globe,
  Layers,
  MapPin,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
  TriangleAlert,
  Waves,
  Wifi,
  WifiOff,
  Zap,
} from "lucide-react";

import AgenticPanel from "./AgenticPanel";
import OperationalSignals from "./OperationalSignals";
import OffsetWellChart from "./OffsetWellChart";
import IssueNotificationPanel from "./IssueNotificationPanel";
import SodirRegistryExplorer from "./SodirRegistryExplorer";
import "./index.css";

const API_URL = "/api";
const ease = [0.22, 1, 0.36, 1];

function formatWellName(id) {
  if (!id) return "";
  return id
    .replace(/^Norway-Statoil-NO\s*/i, "")
    .replace(/_\$47\$_/g, "/")
    .replace(/_/g, " ");
}

function App() {
  const reduceMotion = useReducedMotion();
  const [wells, setWells] = useState([]);
  const [selectedWell, setSelectedWell] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiStatus, setApiStatus] = useState("checking");
  const [sodirStats, setSodirStats] = useState(null);

  const reveal = reduceMotion
    ? {}
    : {
        initial: { opacity: 0, y: 16 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true, amount: 0.1 },
        transition: { duration: 0.45, ease },
      };

  // Load wells on mount
  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      setApiStatus("checking");

      try {
        const [wellsRes, sodirRes] = await Promise.all([
          fetch(`${API_URL}/wells`),
          fetch(`${API_URL}/sodir/stats`).catch(() => null),
        ]);

        if (!wellsRes.ok) throw new Error("Wells request failed");

        const data = await wellsRes.json();
        if (cancelled) return;

        const list = Array.isArray(data.wells) ? data.wells : [];
        setWells(list);
        setSelectedWell((current) =>
          current && list.includes(current)
            ? current
            : list[list.length - 1] || ""
        );

        if (sodirRes && sodirRes.ok) {
          const sData = await sodirRes.json();
          if (!cancelled) setSodirStats(sData);
        }

        setApiStatus("connected");
        setError("");
      } catch {
        if (cancelled) return;
        setApiStatus("disconnected");
        setError("Unable to connect to the NWIS API. Ensure backend server is running on port 8000.");
      }
    }

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  const analyzeWell = async () => {
    if (!selectedWell || loading) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/agentic-analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ well_id: selectedWell }),
      });

      if (!response.ok) {
        throw new Error(`Analysis endpoint returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data);
      setApiStatus("connected");
    } catch (err) {
      setApiStatus("disconnected");
      setError(
        err.message?.startsWith("Analysis endpoint")
          ? err.message
          : "Analysis failed. Please inspect the FastAPI server and backend logs."
      );
    } finally {
      setLoading(false);
    }
  };

  const riskLevel = analysis?.risk?.level || "—";
  // Backend returns risk.probability already as a percentage (e.g. 2.0 = 2.0%)
  const riskProbability = Number(analysis?.risk?.probability ?? 0);
  const probabilityPct = Math.max(0, Math.min(100, riskProbability));

  // Risk ring calculation
  const circleRadius = 54;
  const circumference = 2 * Math.PI * circleRadius;
  const strokeDashoffset = circumference - (probabilityPct / 100) * circumference;

  return (
    <div className="app-shell">
      {/* Sleek Top Navigation Header */}
      <header className="navbar">
        <div className="navbar-left">
          <div className="brand">
            <div className="brand-icon">
              <BrainCircuit size={22} />
            </div>
            <div>
              <h1>DrillIntel</h1>
              <span>Subsurface AI Decision Support</span>
            </div>
          </div>

          <nav className="navbar-nav">
            <div className="nav-item active">
              <Gauge size={16} />
              Operations Dashboard
            </div>
            <div className="nav-item">
              <Target size={16} />
              Well Intelligence
            </div>
            <div className="nav-item">
              <ShieldAlert size={16} />
              Risk Review
            </div>
            <div className="nav-item">
              <Database size={16} />
              Historical RAG
            </div>
          </nav>
        </div>

        <div className="navbar-right">
          <div className="sodir-header-pill" title="Norwegian Offshore Directorate (SODIR) FactMaps WGS84 open-data layer">
            <Globe size={13} className="text-cyan" />
            <span>SODIR · {sodirStats?.total_wellbores ? `${sodirStats.total_wellbores.toLocaleString()} Wellbores` : "9,869 Wellbores"}</span>
          </div>

          <div className={`connection-indicator ${apiStatus}`}>
            <span className="indicator-led" />
            <span className="indicator-label">
              {apiStatus === "connected"
                ? "NWIS ENGINE ONLINE"
                : apiStatus === "checking"
                  ? "CONNECTING..."
                  : "API OFFLINE"}
            </span>
          </div>

          <motion.button
            className="action-analyze-btn"
            onClick={analyzeWell}
            disabled={loading || !selectedWell}
            whileHover={reduceMotion ? {} : { scale: 1.02 }}
            whileTap={reduceMotion ? {} : { scale: 0.98 }}
          >
            <RefreshCw size={15} className={loading ? "spin" : ""} />
            <span>{loading ? "Analyzing telemetry…" : "Analyze well"}</span>
          </motion.button>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="main-content">
        {/* Error Notification Banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="error-glass-banner"
              initial={reduceMotion ? false : { opacity: 0, height: 0, y: -10 }}
              animate={{ opacity: 1, height: "auto", y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              role="alert"
            >
              <TriangleAlert size={18} className="text-amber" />
              <span>{error}</span>
              <button
                className="dismiss-error-btn"
                onClick={() => setError("")}
                aria-label="Dismiss alert"
              >
                ×
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 1. Streamlined, Compact Target Well Header Card */}
        <motion.section className="compact-target-card" {...reveal}>
          <div className="target-card-left">
            <div className="target-pulse-symbol">
              <span className="pulse-ring" />
              <MapPin size={17} />
            </div>

            <div className="target-text-block">
              <div className="target-eyebrow-row">
                <span className="target-eyebrow">ACTIVE TARGET WELL</span>
                <span className="target-field-tag">Volve Field · Block 15/9</span>
              </div>
              <h2 className="target-well-title">
                {selectedWell || (apiStatus === "checking" ? "Discovering wells…" : "No Well Selected")}
              </h2>
              {analysis?.sodir_metadata && (
                <div className="target-sodir-meta-strip">
                  <span className="sodir-verified-pill">
                    <ShieldCheck size={12} className="text-cyan" />
                    SODIR Verified · {analysis.sodir_metadata.wellbore_name}
                  </span>
                  {analysis.sodir_metadata.latitude != null && (
                    <span className="meta-sub-item">
                      <MapPin size={11} />
                      {Number(analysis.sodir_metadata.latitude).toFixed(4)}° N, {Number(analysis.sodir_metadata.longitude).toFixed(4)}° E
                    </span>
                  )}
                  {analysis.sodir_metadata.operator && (
                    <span className="meta-sub-item">
                      {analysis.sodir_metadata.operator}
                    </span>
                  )}
                  {analysis.sodir_metadata.total_depth != null && (
                    <span className="meta-sub-item">
                      TD: {Number(analysis.sodir_metadata.total_depth).toLocaleString()} m
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="target-card-right">
            <div className="well-dropdown-wrapper">
              <label htmlFor="well-select-control">SELECT WELL:</label>
              <div className="select-container">
                <select
                  id="well-select-control"
                  value={selectedWell}
                  onChange={(e) => {
                    setSelectedWell(e.target.value);
                    setAnalysis(null);
                    setError("");
                  }}
                >
                  {!wells.length && <option value="">No wells available</option>}
                  {wells.map((well) => (
                    <option key={well} value={well}>
                      {formatWellName(well) || well}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <span className="well-count-pill">
              <Layers size={13} />
              {wells.length} Available
            </span>
          </div>
        </motion.section>

        {/* 2. Unified Operational Signals Container */}
        <OperationalSignals
          condition={analysis?.current_condition}
          loading={loading}
          reduceMotion={reduceMotion}
        />

        {/* Issue Notification & Unknown Scenario Detection Panel */}
        <IssueNotificationPanel
          issueNotification={analysis?.issue_notification}
          loading={loading}
          reduceMotion={reduceMotion}
        />

        {/* 3. Interactive Agent Mission Control (Risk & Context) */}
        <AgenticPanel
          agentic={analysis?.agentic}
          reduceMotion={reduceMotion}
        />

        {/* 4. Well Intelligence: Risk Gauge & Offset Well Chart */}
        <div className="section-title-bar">
          <div className="section-title-left">
            <span className="section-eyebrow">INTELLIGENCE SUITE</span>
            <h2>Well Intelligence & Offset Analysis</h2>
          </div>
          <span className="section-advisory">
            <ShieldCheck size={14} /> Human review required
          </span>
        </div>

        <section className="dashboard-two-col">
          {/* Left: Upgraded Dynamic Risk Assessment Gauge */}
          <motion.div className="glass-panel risk-gauge-panel" {...reveal}>
            <div className="panel-title-row">
              <div className="panel-title-icon">
                <ShieldAlert size={18} />
              </div>
              <div>
                <h3>Risk Assessment</h3>
                <p>Machine learning classification & incident probability</p>
              </div>
            </div>

            <div className="risk-gauge-body">
              <div className="gauge-meter-wrapper">
                <svg className="gauge-svg" viewBox="0 0 140 140">
                  <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#00F2FE" />
                      <stop offset="100%" stopColor="#0284C7" />
                    </linearGradient>
                    <linearGradient id="gaugeAmberGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#FFB300" />
                      <stop offset="100%" stopColor="#D97706" />
                    </linearGradient>
                    <linearGradient id="gaugeRoseGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#F43F5E" />
                      <stop offset="100%" stopColor="#BE123C" />
                    </linearGradient>
                  </defs>

                  {/* Background Track */}
                  <circle
                    className="gauge-bg-circle"
                    cx="70"
                    cy="70"
                    r={circleRadius}
                  />

                  {/* Dynamic Progress Stroke */}
                  <circle
                    className={`gauge-progress-circle ${String(riskLevel).toLowerCase()}`}
                    cx="70"
                    cy="70"
                    r={circleRadius}
                    strokeDasharray={circumference}
                    strokeDashoffset={analysis ? strokeDashoffset : circumference}
                  />
                </svg>

                <div className="gauge-center-readout">
                  <strong className="gauge-number">
                    {analysis ? `${riskProbability.toFixed(1)}%` : "—"}
                  </strong>
                  <span className="gauge-sublabel">RISK PROB</span>
                </div>
              </div>

              <div className="risk-description-block">
                <span className="card-label">CLASSIFIED LEVEL:</span>
                <div className={`risk-level-tag ${String(riskLevel).toLowerCase()}`}>
                  <span className="level-dot" />
                  <span>{riskLevel}</span>
                </div>

                <p className="risk-explanation">
                  {analysis
                    ? "Evaluated against historical offset drilling conditions and hydraulic thresholds."
                    : "Run analysis to execute the random forest risk predictor on latest parameters."}
                </p>

                <div className="engineering-signoff-badge">
                  <ShieldCheck size={14} />
                  <span>Verified engineer sign-off required</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right: Interactive Offset Well Graph (Recharts) */}
          <motion.div className="glass-panel" {...reveal}>
            <OffsetWellChart offsetWells={analysis?.offset_wells} />
          </motion.div>
        </section>

        {/* 5. Historical RAG Evidence & Recommendations Grid */}
        <section className="dashboard-two-col mt-6">
          {/* Historical RAG Intelligence */}
          <motion.div className="glass-panel" {...reveal}>
            <div className="panel-title-row">
              <div className="panel-title-icon">
                <Database size={18} />
              </div>
              <div>
                <h3>Historical RAG Intelligence</h3>
                <p>Nearest semantic & depth-correlated drilling incidents</p>
              </div>
            </div>

            <div className="rag-events-list">
              {analysis?.historical_events?.length ? (
                analysis.historical_events.slice(0, 5).map((event, index) => {
                  const similarityPct = Number(event.similarity_score ?? 0) * 100;
                  return (
                    <motion.div
                      key={`${event.timestamp}-${index}`}
                      className="rag-event-card"
                      initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <div className="event-card-top">
                        <span className="event-type-pill">{event.event_type || "drilling_event"}</span>
                        <span className="event-similarity-pill">
                          {similarityPct ? `${similarityPct.toFixed(1)}% match` : "Correlated"}
                        </span>
                      </div>

                      <strong className="event-well-id">{formatWellName(event.well_id) || event.well_id}</strong>
                      <p className="event-description">{event.description || "No description recorded."}</p>

                      <div className="event-meta-footer">
                        <span>Depth: {event.depth ?? "—"} m</span>
                        <span>•</span>
                        <span>{event.timestamp ? new Date(event.timestamp).toLocaleDateString() : "Historical"}</span>
                      </div>
                    </motion.div>
                  );
                })
              ) : (
                <div className="empty-panel-state">
                  <Database size={24} className="text-cyan" />
                  <span>Historical incidents will be retrieved and ranked upon analysis.</span>
                </div>
              )}
            </div>
          </motion.div>

          {/* NWIS Recommendations */}
          <motion.div className="glass-panel" {...reveal}>
            <div className="panel-title-row">
              <div className="panel-title-icon">
                <Sparkles size={18} />
              </div>
              <div>
                <h3>NWIS Recommendations</h3>
                <p>Rule-derived and evidence-guided mitigations</p>
              </div>
            </div>

            <div className="recommendations-container">
              {analysis?.recommendations?.length ? (
                analysis.recommendations.map((rec, index) => (
                  <motion.div
                    key={index}
                    className="recommendation-step-card"
                    initial={reduceMotion ? false : { opacity: 0, x: 8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.06 }}
                  >
                    <div className="rec-step-number">
                      {String(index + 1).padStart(2, "0")}
                    </div>
                    <p className="rec-step-text">{rec}</p>
                  </motion.div>
                ))
              ) : (
                <div className="empty-panel-state">
                  <Sparkles size={24} className="text-amber" />
                  <span>Run analysis to generate operational engineering recommendations.</span>
                </div>
              )}

              <div className="decision-advisory-box">
                <div className="advisory-icon-wrap">
                  <ShieldAlert size={19} />
                </div>
                <div>
                  <strong>Operational Decision Support</strong>
                  <p>
                    DrillIntel provides automated advisory assistance. Final drilling parameter
                    adjustments must be validated by the operating supervisor.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* 5. Official SODIR Regional Wellbore Registry Explorer */}
        <SodirRegistryExplorer stats={sodirStats} />

        {/* Sleek Minimal Footer */}
        <footer className="app-footer">
          <div className="footer-brand">
            <span className="footer-mark">DI</span>
            <span>DrillIntel · Intelligent Subsurface Risk Architecture</span>
          </div>
          <span className="footer-copy">
            Deterministic Decision Engine · Human-in-the-Loop Prototype
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;
