# DrillIntel — Intelligent Drilling Risk Analysis



DrillIntel is a prototype decision-support system designed to analyze drilling-well conditions, retrieve relevant historical drilling events, compare offset wells, and present risk-related insights to support drilling engineers.

The project combines drilling data analysis, historical evidence retrieval, a multi-stage agent workflow, and an optional locally hosted Large Language Model (LLM) for evidence synthesis.

> **Disclaimer:** DrillIntel is a research and decision-support prototype. Its outputs are not a substitute for qualified engineering judgment and must not be used as autonomous drilling-control instructions.

## Key Features

- **Well Analysis:** Processes well identifiers and available drilling parameters.
- **Risk Review:** Presents the risk level and probability produced by the existing analysis pipeline.
- **Offset-Well Comparison:** Reviews similar wells and their available depth and similarity information.
- **Historical Event Retrieval:** Retrieves relevant historical drilling records using the existing retrieval pipeline.
- **Agent-Based Workflow:** Runs separate review stages for risk, offset wells, historical events, and recommendations.
- **Optional Local LLM Synthesis:** Integrates with Ollama and the `qwen2.5:3b` model to summarize available evidence.
- **Fallback Handling:** Retains deterministic review results when LLM synthesis is unavailable.
- **Human-in-the-Loop Design:** Requires qualified human review of findings and recommendations.

## System Architecture

```text
Drilling Well Data
        |
        v
Well Analysis API
        |
        +---- Risk Assessment
        |
        +---- Offset-Well Analysis
        |
        +---- Historical Event Retrieval
        |
        +---- Recommendations
                    |
                    v
          Agent Review Workflow
                    |
          +---------+----------+
          |                    |
          v                    v
   Deterministic Reviews   Optional Ollama LLM
          |                    |
          +---------+----------+
                    |
                    v
       Evidence-Based Results
                    |
                    v
          Engineer Review
```

The LLM is an optional synthesis component. The current agent workflow uses deterministic rules to select and run review stages; it is not an autonomous LLM planner.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite |
| Backend API | Python, FastAPI |
| API Server | Uvicorn |
| Historical Evidence Retrieval | Existing RAG pipeline with embeddings and FAISS |
| Local LLM Integration | Ollama |
| LLM Model | Qwen 2.5 3B |
| Version Control | Git and GitHub |

## Project Structure

```text
eRTMAC-NWIS-main/
├── backend/
│   ├── agents/
│   │   ├── agent_runtime.py
│   │   └── llm_planner.py
│   ├── ai/
│   │   └── rag_search.py
│   └── main.py
├── frontend/
│   ├── package.json
│   └── ...
├── README.md
└── .gitignore
```

*This is a simplified overview. Refer to the repository for the complete project structure.*

## Prerequisites

Install the following before running the project:

- Python 3.11 or a compatible Python version supported by the project's dependencies
- Node.js and npm
- Git
- Ollama, if you want to enable local LLM synthesis
- The Python and frontend dependencies specified by the project

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/vibhu-006/DrillIntel.git
cd DrillIntel
```

### 2. Set up the Python backend

From the project root, create and activate a virtual environment:

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies using the project's dependency file, if present. For example, if the repository contains `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Start the backend:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The API should be available at:

- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

### 3. Set up the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --port 3000
```

Open the local frontend URL shown by Vite, normally:

http://localhost:3000



Optional environment variables:

```text
DRILLINTEL_LLM_MODEL=qwen2.5:3b
OLLAMA_URL=http://127.0.0.1:11434
```

LLM synthesis may be unavailable if Ollama is stopped, the model is missing, or generation exceeds the configured timeout. The deterministic review workflow is designed to retain its results in that situation.

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Check backend health |
| `/wells` | GET | Retrieve available well information |
| `/analyze` | POST | Run the existing well-analysis pipeline |
| `/agentic-analyze` | POST | Run the analysis with the agent review workflow |
