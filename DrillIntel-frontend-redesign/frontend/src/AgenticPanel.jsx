
import { motion } from "motion/react";
import {
  Activity,
  CheckCircle2,
  CircleAlert,
  Clock3,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import "./agentic-panel.css";

const statusIcon = {
  complete: CheckCircle2,
  warning: CircleAlert,
  failed: XCircle,
};

const formatLabel = (value) =>
  String(value ?? "Unknown").replaceAll("_", " ");

export default function AgenticPanel({ agentic }) {
  const agents = Array.isArray(agentic?.agents) ? agentic.agents : [];
  const limitations = Array.isArray(agentic?.limitations)
    ? agentic.limitations
    : [];

  return (
    <section className="agentic-panel">
      <header className="agentic-header">
        <div className="agentic-mark">
          <Activity size={20} />
        </div>

        <div>
          <p className="agentic-eyebrow">
            AGENTIC INTELLIGENCE / EXECUTION TRACE
          </p>
          <h3>Agent Mission Control</h3>
          <p className="agentic-subtitle">
            Evidence-driven orchestration · Human approval remains required
          </p>
        </div>

        <span
          className={`agentic-status ${formatLabel(
            agentic?.overall_status ?? "idle"
          )}`}
        >
          {formatLabel(agentic?.overall_status ?? "idle")}
        </span>
      </header>

      {!agents.length ? (
        <div className="agentic-empty">
          <ShieldCheck size={22} />
          <strong>Ready for analysis</strong>
          <p>Agent execution details will appear here after analysis.</p>
        </div>
      ) : (
        <div className="agentic-timeline">
          {agents.map((agent, i) => {
            const status = String(agent?.status ?? "warning").toLowerCase();
            const Icon = statusIcon[status] ?? Clock3;
            const result = agent?.result ?? {};
            const content =
              result?.content ??
              result?.finding ??
              agent?.detail ??
              "No additional details available.";

            return (
              <motion.div
                key={`${agent?.stage ?? agent?.name ?? "stage"}-${i}`}
                className="agentic-step"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <div className="agentic-step-icon">
                  <Icon size={17} />
                </div>

                <div className="agentic-step-body">
                  <div className="agentic-step-top">
                    <strong>
                      {agent?.name ?? agent?.title ?? "Review stage"}
                    </strong>
                    <span>
                      {formatLabel(agent?.tool ?? agent?.agent ?? agent?.stage)}
                    </span>
                  </div>

                  <p>{agent?.detail ?? "No details available."}</p>

                  {agent?.reason && (
                    <p className="agentic-step-reason">{agent.reason}</p>
                  )}

                  {content && (
                    <details>
                      <summary>Inspect result</summary>
                      <pre className="agentic-result">
                        {typeof content === "string"
                          ? content
                          : JSON.stringify(content, null, 2)}
                      </pre>
                    </details>
                  )}

                  {Array.isArray(agent?.evidence) &&
                    agent.evidence.length > 0 && (
                      <details>
                        <summary>
                          Inspect evidence ({agent.evidence.length})
                        </summary>
                        <pre className="agentic-result">
                          {JSON.stringify(agent.evidence, null, 2)}
                        </pre>
                      </details>
                    )}
                </div>

                <span
                  className={`agentic-step-state ${formatLabel(status)}`}
                >
                  {formatLabel(status)}
                </span>
              </motion.div>
            );
          })}
        </div>
      )}

      <footer className="agentic-footer">
        <ShieldCheck size={16} />
        <span>
          Decision support only. Qualified human review is required.
        </span>
      </footer>

      {limitations.length > 0 && (
        <details className="agentic-limitations">
          <summary>Workflow limitations ({limitations.length})</summary>
          <ul>
            {limitations.map((item, i) => (
              <li key={`${i}-${item}`}>{item}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
