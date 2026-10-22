import AgenticPanel from "./AgenticPanel";
import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Database,
  Gauge,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
  TriangleAlert,
  Waves,
  Wifi,
  WifiOff,
} from "lucide-react";
import "./index.css";

const API_URL = "/api";

const ease = [0.22, 1, 0.36, 1];

function App() {
  const reduceMotion = useReducedMotion();
  const [wells, setWells] = useState([]);
  const [selectedWell, setSelectedWell] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiStatus, setApiStatus] = useState("checking");
  const [activity, setActivity] = useState([]);

  const reveal = reduceMotion
    ? {}
    : {
        initial: { opacity: 0, y: 18 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true, amount: 0.12 },
        transition: { duration: 0.55, ease },
      };

  useEffect(() => {
    let cancelled = false;

    async function loadWells() {
      setApiStatus("checking");

      try {
        const response = await fetch(`${API_URL}/wells`);
        if (!response.ok) throw new Error("Wells request failed");

        const data = await response.json();
        if (cancelled) return;

        const list = Array.isArray(data.wells) ? data.wells : [];
        setWells(list);
        setSelectedWell((current) =>
          current && list.includes(current)
            ? current
            : list[list.length - 1] || ""
        );
        setApiStatus("connected");
        setError("");
      } catch {
        if (cancelled) return;
        setApiStatus("disconnected");
        setError("Unable to connect to the NWIS API. Check that the backend is running and the frontend proxy is configured.");
      }
    }

    loadWells();

    return () => {
      cancelled = true;
    };
  }, []);

  const addActivity = (message, status = "complete") => {
    setActivity((current) => [
      ...current,
      {
        id: `${Date.now()}-${Math.random()}`,
        message,
        status,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      },
    ]);
  };

  const analyzeWell = async () => {
    if (!selectedWell || loading) return;

    setLoading(true);
    setError("");
    setActivity([]);
    addActivity(`Analysis request prepared for ${selectedWell}`);
    addActivity("Sending request to the NWIS analysis endpoint", "running");

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

      setActivity((current) =>
        current.map((item) =>
          item.status === "running"
            ? { ...item, status: "complete", message: "NWIS endpoint responded successfully" }
            : item
        )
      );
      addActivity("Analysis response received and dashboard updated");
    } catch (err) {
      setApiStatus("disconnected");
      setError(
        err.message?.startsWith("Analysis endpoint")
          ? err.message
          : "Analysis failed. Check the FastAPI server, frontend proxy, and backend logs."
      );
      addActivity("Request failed — inspect the API error and backend logs", "error");
    } finally {
      setLoading(false);
    }
  };

  const riskLevel = analysis?.risk?.level || "—";
  const riskProbability = Number(analysis?.risk?.probability ?? 0);
  const probability = Math.max(0, Math.min(100, riskProbability));

  return (
    <div className="app-shell">
      <motion.aside
        className="sidebar"
        initial={reduceMotion ? false : { opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.55, ease }}
      >
        <div className="brand">
          <motion.div
            className="brand-icon"
            whileHover={reduceMotion ? {} : { rotate: -8, scale: 1.06 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <BrainCircuit size={25} />
          </motion.div>
          <div>
            <h1>DrillIntel</h1>
            <span>Drilling Intelligence</span>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>
        <nav>
          <div className="nav-item active">
            <Gauge size={19} />
            Dashboard
          </div>
          <div className="nav-item">
            <Target size={19} />
            Well Intelligence
          </div>
          <div className="nav-item">
            <ShieldAlert size={19} />
            Risk Analysis
          </div>
          <div className="nav-item">
            <Database size={19} />
            Historical Events
          </div>
        </nav>

        <div className="sidebar-spacer" />

        <div className={`sidebar-status status-${apiStatus}`}>
          {apiStatus === "connected" ? (
            <Wifi size={18} />
          ) : (
            <WifiOff size={18} />
          )}
          <div>
            <strong>NWIS Engine</strong>
            <span>
              {apiStatus === "connected"
                ? "API Connected"
                : apiStatus === "checking"
                  ? "Checking connection…"
                  : "API Disconnected"}
            </span>
          </div>
          <span className="status-dot" />
        </div>

        <div className="sidebar-footer">
          <span className="sidebar-footer-mark">DI</span>
          <span>DRILLINTEL <span className="muted">· PROTOTYPE</span></span>
        </div>
      </motion.aside>

      <main className="main-content">
        <motion.header
          className="topbar"
          initial={reduceMotion ? false : { opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease }}
        >
          <div>
            <p className="eyebrow">INTELLIGENCE / OVERVIEW</p>
            <h2>Drilling Operations</h2>
            <p className="topbar-subtitle">
              Geological context. Risk visibility. Evidence-led decisions.
            </p>
          </div>

          <div className="topbar-right">
            <div className={`live-pill connection-${apiStatus}`}>
              <span />
              {apiStatus === "connected"
                ? "API CONNECTED"
                : apiStatus === "checking"
                  ? "CONNECTING"
                  : "API OFFLINE"}
            </div>
            <motion.button
              className="refresh-button"
              onClick={analyzeWell}
              disabled={loading || !selectedWell}
              whileHover={reduceMotion ? {} : { y: -2, scale: 1.015 }}
              whileTap={reduceMotion ? {} : { scale: 0.97 }}
            >
              <RefreshCw
                size={17}
                className={loading ? "spin" : ""}
              />
              {loading ? "Analyzing…" : "Analyze well"}
            </motion.button>
          </div>
        </motion.header>

        <AnimatePresence>
          {error && (
            <motion.div
              className="error-box"
              initial={reduceMotion ? false : { opacity: 0, height: 0, y: -8 }}
              animate={{ opacity: 1, height: "auto", y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              role="alert"
            >
              <TriangleAlert size={20} />
              <span>{error}</span>
              <button
                className="dismiss-error"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                ×
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.section className="hero-card" {...reveal}>
          <div className="hero-left">
            <motion.div
              className="hero-icon"
              animate={
                reduceMotion
                  ? {}
                  : { y: [0, -3, 0], opacity: [0.9, 1, 0.9] }
              }
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
            >
              <Waves size={27} />
            </motion.div>
            <div>
              <span className="card-label">TARGET WELL / ACTIVE SELECTION</span>
              <h3>{selectedWell || (apiStatus === "checking" ? "Loading wells…" : "No well selected")}</h3>
              <p>
                Review drilling conditions, evaluate the returned risk assessment,
                and explore historical context.
              </p>
            </div>
          </div>

          <div className="well-selector">
            <label htmlFor="well-select">Select well</label>
            <select
              id="well-select"
              value={selectedWell}
              onChange={(event) => {
                setSelectedWell(event.target.value);
                setAnalysis(null);
                setActivity([]);
                setError("");
              }}
            >
              {!wells.length && <option value="">No wells available</option>}
              {wells.map((well) => (
                <option key={well} value={well}>{well}</option>
              ))}
            </select>
            <span className="selector-caption">
              {wells.length} well{wells.length === 1 ? "" : "s"} available from API
            </span>
          </div>
        </motion.section>

        <motion.div className="section-heading" {...reveal}>
          <div>
            <span className="eyebrow">LIVE OVERVIEW</span>
            <h3>Operational signals</h3>
          </div>
          <span className="data-context">
            {analysis ? "Values from latest API response" : "Awaiting analysis"}
          </span>
        </motion.div>

        <motion.section
          className="metrics-grid"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: {
              transition: reduceMotion ? {} : { staggerChildren: 0.08 },
            },
          }}
        >
          <MetricCard
            reduceMotion={reduceMotion}
            icon={<MapPin />}
            label="CURRENT DEPTH"
            value={analysis ? formatMetric(analysis.current_condition?.depth, 1, " m") : "—"}
            sub="Measured depth"
          />
          <MetricCard
            reduceMotion={reduceMotion}
            icon={<Activity />}
            label="WEIGHT ON BIT"
            value={analysis ? formatMetric(analysis.current_condition?.wob, 1) : "—"}
            sub="WOB · API units"
          />
          <MetricCard
            reduceMotion={reduceMotion}
            icon={<TrendingUp />}
            label="TORQUE"
            value={analysis ? formatMetric(analysis.current_condition?.torque, 2) : "—"}
            sub="Current reading"
          />
          <MetricCard
            reduceMotion={reduceMotion}
            icon={<Waves />}
            label="PUMP"
            value={analysis ? formatMetric(analysis.current_condition?.pump, 1) : "—"}
            sub="Pump activity"
          />
        </motion.section>

        <motion.div className="section-heading" {...reveal}>
          <div>
            <span className="eyebrow">RISK & CONTEXT</span>
            <AgenticPanel agentic={analysis?.agentic} />
            <h3>Well intelligence</h3>
          </div>
          <span className="data-context">Decision support · Human review required</span>
        </motion.div>

        <section className="dashboard-grid">
          <motion.div className="panel risk-panel" {...reveal}>
            <PanelTitle
              icon={<ShieldAlert />}
              title="Risk assessment"
              subtitle="Prediction returned by the NWIS API"
            />

            <div className="risk-content">
              <motion.div
                className={`risk-ring ${String(riskLevel).toLowerCase()}`}
                animate={
                  reduceMotion || !analysis
                    ? {}
                    : { scale: [1, 1.025, 1] }
                }
                transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
                style={{
                  "--risk-progress": `${analysis ? probability : 0}%`,
                }}
              >
                <div>
                  <motion.strong
                    key={analysis ? probability : "empty"}
                    initial={reduceMotion ? false : { opacity: 0, y: 7 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35 }}
                  >
                    {analysis ? `${riskProbability.toFixed(1)}%` : "—"}
                  </motion.strong>
                  <span>RISK</span>
                </div>
              </motion.div>

              <div className="risk-info">
                <span className="card-label">CURRENT RISK LEVEL</span>
                <h3 className={String(riskLevel).toLowerCase()}>
                  {riskLevel}
                </h3>
                <p>
                  {analysis
                    ? "Review the model output alongside source data and engineering judgment."
                    : "Run an analysis to load the backend risk result."}
                </p>
                <div className="human-review-note">
                  <ShieldAlert size={15} />
                  Human engineering review required
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div className="panel" {...reveal}>
            <PanelTitle
              icon={<Target />}
              title="Offset well intelligence"
              subtitle="Similarity ranking returned by the API"
            />

            <div className="offset-list">
              {analysis?.offset_wells?.length ? (
                analysis.offset_wells.map((well, index) => {
                  const score = Number(well.similarity_score) * 100;
                  const safeScore = Math.max(0, Math.min(100, score));

                  return (
                    <motion.div
                      className="offset-row"
                      key={well.well_id}
                      initial={reduceMotion ? false : { opacity: 0, x: 12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: reduceMotion ? 0 : index * 0.08, duration: 0.35 }}
                      whileHover={reduceMotion ? {} : { x: 4 }}
                    >
                      <div className="rank">{String(index + 1).padStart(2, "0")}</div>
                      <div className="offset-main">
                        <strong>{well.well_id}</strong>
                        <div
                          className="progress"
                          role="progressbar"
                          aria-label={`Similarity for ${well.well_id}`}
                          aria-valuenow={safeScore}
                          aria-valuemin={0}
                          aria-valuemax={100}
                        >
                          <motion.span
                            initial={{ width: 0 }}
                            animate={{ width: `${safeScore}%` }}
                            transition={{ duration: reduceMotion ? 0 : 0.8, delay: reduceMotion ? 0 : index * 0.08, ease }}
                          />
                        </div>
                      </div>
                      <strong className="score">
                        {Number.isFinite(score) ? `${score.toFixed(1)}%` : "—"}
                      </strong>
                      <ChevronRight size={17} />
                    </motion.div>
                  );
                })
              ) : (
                <EmptyState text="Run an analysis to view the returned offset wells." />
              )}
            </div>
          </motion.div>
        </section>

        <section className="dashboard-grid">
          <motion.div className="panel" {...reveal}>
            <PanelTitle
              icon={<Database />}
              title="Historical RAG intelligence"
              subtitle="Historical events returned by the API"
            />

            <div className="event-list">
              {analysis?.historical_events?.length ? (
                analysis.historical_events.slice(0, 5).map((event, index) => (
                  <motion.div
                    className="event-card"
                    key={`${event.timestamp}-${index}`}
                    initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: reduceMotion ? 0 : index * 0.07, duration: 0.35 }}
                  >
                    <div className="event-number">{String(index + 1).padStart(2, "0")}</div>
                    <div className="event-main">
                      <div className="event-top">
                        <span className="event-type">{event.event_type || "Historical event"}</span>
                        <span className="similarity">
                          {Number.isFinite(Number(event.similarity_score))
                            ? `${(Number(event.similarity_score) * 100).toFixed(1)}% match`
                            : "Similarity unavailable"}
                        </span>
                      </div>
                      <strong>{event.well_id || "Unknown well"}</strong>
                      <p>{event.description || "No event description provided."}</p>
                      <small>
                        Depth: {event.depth ?? "Unavailable"} m · {event.timestamp || "Date unavailable"}
                      </small>
                    </div>
                  </motion.div>
                ))
              ) : (
                <EmptyState text="Historical events will appear here after analysis." />
              )}
            </div>
          </motion.div>

          <motion.div className="panel recommendation-panel" {...reveal}>
            <PanelTitle
              icon={<Sparkles />}
              title="NWIS recommendations"
              subtitle="Guidance returned by the backend"
            />

            <div className="recommendation-list">
              {analysis?.recommendations?.length ? (
                analysis.recommendations.map((recommendation, index) => (
                  <motion.div
                    className="recommendation"
                    key={`${index}-${recommendation}`}
                    initial={reduceMotion ? false : { opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: reduceMotion ? 0 : index * 0.08 }}
                  >
                    <div>{String(index + 1).padStart(2, "0")}</div>
                    <p>{recommendation}</p>
                  </motion.div>
                ))
              ) : (
                <EmptyState text="Run analysis to retrieve recommendations." />
              )}
            </div>

            <div className="decision-box">
              <Sparkles size={20} />
              <div>
                <strong>Decision support</strong>
                <span>
                  {analysis
                    ? "Review findings before taking operational action."
                    : "Waiting for an analysis response."}
                </span>
              </div>
            </div>
          </motion.div>
        </section>

        <section className="dashboard-grid investigation-grid">
          <motion.div className="panel investigation-panel" {...reveal}>
            <PanelTitle
              icon={<BrainCircuit />}
              title="Investigation activity"
              subtitle="Transparent view of the frontend-to-API request"
            />

            <div className="agent-status-line">
              <span className={`agent-orb ${loading ? "is-running" : ""}`}>
                <BrainCircuit size={19} />
              </span>
              <div>
                <strong>
                  {loading
                    ? "Request in progress"
                    : analysis
                      ? "Response received"
                      : "Ready to investigate"}
                </strong>
                <span>
                  {loading
                    ? `Waiting for the analysis endpoint for ${selectedWell}`
                    : analysis
                      ? "The dashboard is showing the latest returned analysis."
                      : "Select a well and run Analyze well to begin."}
                </span>
              </div>
              {loading && <span className="activity-spinner" />}
            </div>

            <div className="activity-timeline">
              <AnimatePresence initial={false}>
                {activity.map((item) => (
                  <motion.div
                    className={`activity-item activity-${item.status}`}
                    key={item.id}
                    initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.25 }}
                  >
                    <div className="activity-marker">
                      {item.status === "complete" ? (
                        <CheckCircle2 size={16} />
                      ) : item.status === "error" ? (
                        <CircleAlert size={16} />
                      ) : (
                        <span className="activity-spinner" />
                      )}
                    </div>
                    <div className="activity-copy">
                      <span>{item.message}</span>
                      <small>{item.time}</small>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {!activity.length && (
                <div className="activity-empty">
                  <Activity size={18} />
                  <span>Request events will appear here when you run an analysis.</span>
                </div>
              )}
            </div>

            <div className="activity-disclaimer">
              This timeline reports actual request status. Specialist agent execution
              and evidence verification must be implemented in the backend before
              they can be reported here.
            </div>
          </motion.div>

          <motion.div className="panel system-panel" {...reveal}>
            <PanelTitle
              icon={<Activity />}
              title="System status"
              subtitle="Current frontend connection checks"
            />

            <div className="system-status-row">
              <span className={`system-status-icon system-${apiStatus}`}>
                {apiStatus === "connected" ? <CheckCircle2 size={18} /> : <CircleAlert size={18} />}
              </span>
              <div>
                <strong>Wells endpoint</strong>
                <span>{apiStatus === "connected" ? "Responding" : apiStatus === "checking" ? "Checking…" : "Unavailable"}</span>
              </div>
              <span className={`status-label status-label-${apiStatus}`}>
                {apiStatus === "connected" ? "CONNECTED" : apiStatus === "checking" ? "CHECKING" : "OFFLINE"}
              </span>
            </div>

            <div className="system-status-row">
              <span className={`system-status-icon ${analysis ? "system-connected" : "system-idle"}`}>
                {analysis ? <CheckCircle2 size={18} /> : <Activity size={18} />}
              </span>
              <div>
                <strong>Analysis result</strong>
                <span>{analysis ? "Result loaded" : "No result loaded"}</span>
              </div>
              <span className={`status-label ${analysis ? "status-label-connected" : ""}`}>
                {analysis ? "READY" : "IDLE"}
              </span>
            </div>

            <div className="system-footnote">
              <ShieldAlert size={16} />
              <span>Decision support only. Validate results with a qualified drilling engineer.</span>
            </div>
          </motion.div>
        </section>

        <footer>
          <span>DrillIntel · Geological-aware drilling intelligence</span>
          <span>Prototype · Human engineering review required</span>
        </footer>
      </main>
    </div>
  );
}

function formatMetric(value, decimals, suffix = "") {
  const number = Number(value);
  return value !== null && value !== undefined && Number.isFinite(number)
    ? `${number.toFixed(decimals)}${suffix}`
    : "—";
}

function MetricCard({ icon, label, value, sub, reduceMotion }) {
  return (
    <motion.div
      className="metric-card"
      variants={{
        hidden: { opacity: 0, y: 16 },
        visible: { opacity: 1, y: 0 },
      }}
      transition={{ duration: 0.45, ease }}
      whileHover={reduceMotion ? {} : { y: -4, transition: { duration: 0.2 } }}
    >
      <div className="metric-icon">{icon}</div>
      <div className="metric-copy">
        <span>{label}</span>
        <motion.strong
          key={value}
          initial={reduceMotion ? false : { opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          {value}
        </motion.strong>
        <small>{sub}</small>
      </div>
    </motion.div>
  );
}

function PanelTitle({ icon, title, subtitle }) {
  return (
    <div className="panel-title">
      <div className="panel-title-icon">{icon}</div>
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

function EmptyState({ text }) {
  return (
    <div className="empty-state">
      <Activity size={20} />
      <span>{text}</span>
    </div>
  );
}

export default App;


