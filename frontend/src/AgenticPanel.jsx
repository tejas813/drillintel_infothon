import { motion } from "motion/react";
import { Activity, CheckCircle2, CircleAlert, Clock3, ShieldCheck, XCircle } from "lucide-react";
import "./agentic-panel.css";

const statusIcon = { complete: CheckCircle2, warning: CircleAlert, failed: XCircle };

export default function AgenticPanel({ agentic }) {
  const agents = agentic?.agents ?? [];
  return <section className="agentic-panel">
    <header className="agentic-header">
      <div className="agentic-mark"><Activity size={20}/></div>
      <div><p className="agentic-eyebrow">AGENTIC INTELLIGENCE / EXECUTION TRACE</p>
        <h3>Agent Mission Control</h3>
        <p className="agentic-subtitle">Evidence-driven orchestration · Human approval remains in control</p></div>
      <span className={`agentic-status ${agentic?.overall_status ?? "idle"}`}>{agentic?.overall_status ?? "Awaiting run"}</span>
    </header>
    {!agents.length ? <div className="agentic-empty"><ShieldCheck size={22}/><div><strong>Ready to orchestrate</strong><p>Run an analysis to inspect agent trace, evidence, and limitations.</p></div></div>
    : <div className="agentic-timeline">{agents.map((agent,i)=>{const Icon=statusIcon[agent.status]??Clock3;return <motion.article key={`${agent.agent}-${i}`} className={`agentic-step ${agent.status}`} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.22,delay:i*.045}}>
      <div className="agentic-step-icon"><Icon size={17}/></div><div className="agentic-step-body">
      <div className="agentic-step-top"><strong>{agent.title}</strong><span>{agent.agent.replaceAll("_"," ")}</span></div><p>{agent.summary}</p>
      {!!agent.evidence?.length && <details><summary>Inspect evidence ({agent.evidence.length})</summary><ul>{agent.evidence.map((item,j)=><li key={j}>{item}</li>)}</ul></details>}
      </div><span className={`agentic-step-state ${agent.status}`}>{agent.status}</span></motion.article>})}</div>}
    <footer className="agentic-footer"><ShieldCheck size={16}/><span>Decision support only. Workflow trace verifies outputs, not physical well safety.</span></footer>
    {!!agentic?.limitations?.length && <details className="agentic-limitations"><summary>Workflow scope and limitations</summary><ul>{agentic.limitations.map((x,i)=><li key={i}>{x}</li>)}</ul></details>}
  </section>;
}
