eRTMAC-NWIS

Nearby Wells Intelligence System

eRTMAC-NWIS is an AI-powered Offset Well Intelligence and Drilling Decision Support Platform designed to assist drilling operations by combining historical well data, trajectory similarity, drilling-event intelligence, machine learning, and Retrieval-Augmented Generation (RAG).

The system transforms raw drilling data into actionable intelligence for drilling engineers through an integrated web dashboard.

⸻

🚀 Project Overview

During drilling operations, engineers often need to understand:

* Which historical wells are most similar to the current well?
* How did similar wells behave at comparable depths?
* Were there previous pressure, gas, or well-control events?
* What is the current predicted operational risk?
* What historical information should be reviewed before continuing operations?
* What decision-support recommendations can be generated from available data?

eRTMAC-NWIS addresses these requirements through a unified AI pipeline.

Core Workflow

                    WITSML / Drilling Data
                            │
                            ▼
                  ┌─────────────────────┐
                  │   Data Processing   │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
     Trajectory         Drilling Events    Drilling Parameters
          │                  │                  │
          ▼                  │                  ▼
   Offset Well              │             Risk Features
   Intelligence             │                  │
          │                  │                  ▼
          │                  │            ML Risk Model
          │                  │                  │
          ▼                  ▼                  ▼
       Similarity       Historical RAG     Risk Prediction
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                    Recommendation Engine
                             │
                             ▼
                    NWIS Decision Engine
                             │
                             ▼
                       FastAPI Backend
                             │
                             ▼
                     React Dashboard

⸻

✨ Key Features

1. Offset Well Intelligence

The system identifies and ranks historical wells based on trajectory similarity.

Trajectory comparison uses:

* Measured Depth (MD)
* Inclination
* Azimuth
* True Vertical Depth (TVD)
* Normalized trajectory profiles

This allows the system to identify wells with similar drilling trajectories.

⸻

2. Drilling Risk Prediction

A Random Forest Machine Learning model evaluates available drilling parameters and generates a risk probability.

Current model features include:

* Depth
* BITDEP
* VDEPTH
* WOB
* Torque
* TQ / TQ current parameters
* Flow In
* Flow Out
* Mud Weight In
* Mud Weight Out
* ECD
* Pump
* Pump Power

The model classifies the predicted risk into:

LOW
MEDIUM
HIGH

⸻

3. Drilling Event Intelligence

The system extracts historical drilling events from WITSML XML files.

The event-processing layer identifies information such as:

* Event type
* Well
* Measured depth
* Timestamp
* Event description
* Event classification

Examples include:

Pressure Events
Gas Events
Well-Control Events
Drilling Events

⸻

🧠 4. RAG-Based Historical Intelligence

eRTMAC-NWIS uses Retrieval-Augmented Generation (RAG) concepts to retrieve historically relevant drilling events.

Historical events are converted into vector embeddings using:

SentenceTransformers – all-MiniLM-L6-v2

The embeddings are indexed using:

FAISS

A natural-language query can then retrieve semantically similar historical events.

Example Query

pressure event during drilling high pump pressure and flow changes

The system returns:

* Similarity score
* Historical well
* Event type
* Measured depth
* Timestamp
* Event description

This allows engineers to quickly access relevant historical drilling experience.

⸻

💡 5. Recommendation Engine

The recommendation engine combines available:

* Risk prediction
* Historical events
* Drilling depth
* Operational context

to generate decision-support recommendations.

Example:

Historical pressure-related events were found.
Review pump pressure, flow behaviour, mud parameters
and previous offset-well responses before continuing operations.

The recommendations are intended to support engineering review rather than replace engineering judgment.

⸻

🖥️ 6. Interactive Dashboard

The React dashboard provides a visual interface for the complete NWIS system.

The current UI uses a modern neumorphic design with bright cyan, blue, purple, green, orange, and red accents.

Dashboard sections include:

Target Well

Displays the selected well being analyzed.

Current Drilling Condition

Displays:

* Current depth
* WOB
* Torque
* Pump activity
* Flow information

Risk Assessment

Displays:

* Risk probability
* Risk level
* AI prediction status

Offset Well Intelligence

Displays ranked trajectory-similar historical wells.

Historical RAG Intelligence

Displays semantically similar historical drilling events.

NWIS Recommendation

Displays AI-assisted decision-support recommendations.

⸻

🏗️ System Architecture

┌───────────────────────────────────────────────┐
│              eRTMAC-NWIS Platform             │
├───────────────────────────────────────────────┤
│                                               │
│  WITSML Data                                  │
│      │                                        │
│      ├──► Well / Trajectory Processing        │
│      │             │                          │
│      │             ▼                          │
│      │      Offset Well Intelligence           │
│      │                                        │
│      ├──► Drilling Event Extraction           │
│      │             │                          │
│      │             ▼                          │
│      │        RAG / FAISS                     │
│      │                                        │
│      └──► Drilling Parameters                 │
│                    │                          │
│                    ▼                          │
│             Risk Feature Engineering           │
│                    │                          │
│                    ▼                          │
│             Random Forest Model                │
│                    │                          │
│                    ▼                          │
│             Risk Prediction                    │
│                    │                          │
│                    └──────────┐               │
│                               ▼               │
│                    Recommendation Engine      │
│                               │               │
│                               ▼               │
│                        FastAPI Backend        │
│                               │               │
│                               ▼               │
│                        React Dashboard        │
│                                               │
└───────────────────────────────────────────────┘

⸻

📂 Project Structure

eRTMAC-NWIS/
│
├── backend/
│   │
│   ├── ai/
│   │   ├── risk_features.py
│   │   ├── risk_model.py
│   │   ├── risk_predictor.py
│   │   ├── recommendation_engine.py
│   │   ├── build_rag_index.py
│   │   ├── rag_search.py
│   │   ├── rag_assistant.py
│   │   └── nwis_pipeline.py
│   │
│   ├── data/
│   │   ├── witsml_parser.py
│   │   ├── well_inventory.py
│   │   ├── well_locations.py
│   │   └── drilling_parameters.py
│   │
│   ├── events/
│   │   ├── witsml_events.py
│   │   └── event_depth_mapper.py
│   │
│   ├── offset/
│   │   ├── offset_engine.py
│   │   ├── trajectory_similarity.py
│   │   ├── spatial.py
│   │   └── master_ranking.py
│   │
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── index.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── models/
├── notebooks/
├── docs/
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md

⸻

⚙️ Installation

Requirements

Before running the project, install:

* Python 3.11+
* Node.js 18+
* npm
* Git

Verify the installations:

python3 --version
node --version
npm --version
git --version

⸻

📥 Clone the Repository

Clone the project from GitHub:

git clone https://github.com/kriishna9/eRTMAC-NWIS.git

Enter the project directory:

cd eRTMAC-NWIS

⸻

🐍 Backend Setup

Create a Python virtual environment:

python3 -m venv .venv

Activate it on macOS/Linux:

source .venv/bin/activate

Install Python dependencies:

pip install -r requirements.txt

If required, install the major AI/backend packages:

pip install pandas numpy scikit-learn fastapi uvicorn faiss-cpu sentence-transformers

Verify:

python3 -c "import pandas, numpy, sklearn, fastapi, faiss, sentence_transformers; print('Backend dependencies OK')"

⸻

🛢️ Dataset

The current prototype uses publicly available Volve drilling data as the development and validation dataset.

The Volve dataset is public Norwegian/Equinor drilling data and is not proprietary Oil India drilling data.

Clone the public drilling repository into the external data directory:

git clone https://github.com/f0nzie/volve-drilling.git data/external/volve-drilling

⸻

🔄 Data Processing Pipeline

After obtaining the dataset, process the WITSML information.

Trajectory Processing

Extract well trajectories:

python3 backend/data/witsml_parser.py

Well Inventory

Generate well inventory:

python3 backend/data/well_inventory.py

Well Location Processing

Attempt to extract available coordinates:

python3 backend/data/well_locations.py

If spatial coordinates are unavailable, the system continues using trajectory/depth-based intelligence.

Drilling Parameters

Extract drilling parameters:

python3 backend/data/drilling_parameters.py

Drilling Events

Extract historical drilling events:

python3 backend/events/witsml_events.py

Event Depth Mapping

Map historical events to trajectory depth:

python3 backend/events/event_depth_mapper.py

⸻

🤖 Risk Prediction Setup

Generate the risk feature dataset:

python3 backend/ai/risk_features.py

Train and evaluate the Random Forest model:

python3 backend/ai/risk_model.py

The resulting model produces a probability-based drilling risk assessment.

⸻

🔎 RAG Setup

Build the historical event vector index:

python3 backend/ai/build_rag_index.py

The RAG system uses:

SentenceTransformers
        ↓
all-MiniLM-L6-v2
        ↓
Vector Embeddings
        ↓
FAISS
        ↓
Historical Event Search

Test the semantic search:

python3 backend/ai/rag_search.py

Test the RAG decision-support assistant:

python3 backend/ai/rag_assistant.py

⸻

🧠 Run the Complete NWIS Pipeline

The complete AI pipeline can be tested with:

python3 backend/ai/nwis_pipeline.py

The pipeline combines:

Target Well
     ↓
Offset Well Similarity
     ↓
Risk Prediction
     ↓
Historical RAG
     ↓
Recommendation Engine
     ↓
NWIS Decision

⸻

🚀 FastAPI Backend

Start the backend from the project root:

uvicorn backend.main:app --reload

The API will be available at:

http://127.0.0.1:8000

Health check:

http://127.0.0.1:8000/health

⸻

📚 API Documentation

FastAPI automatically provides interactive Swagger documentation.

Open:

http://127.0.0.1:8000/docs

Current API endpoints:

GET  /
GET  /health
GET  /wells
POST /analyze

⸻

🛢️ Analyze a Well

The main analysis endpoint is:

POST /analyze

Example request:

{
  "well_id": "Norway-Statoil-NO 15_$47$_9-F-9"
}

The API returns:

Target Well
Current Drilling Condition
Risk Prediction
Offset Well Intelligence
Historical RAG Events
Recommendations

⸻

🌐 React Frontend

Open another terminal and navigate to:

cd frontend

Install dependencies:

npm install

Install the icon library:

npm install lucide-react

Start the frontend:

npm run dev

The dashboard will normally be available at:

http://localhost:5173

⸻

🔌 Frontend and Backend Connection

The React application communicates with FastAPI through the Vite development proxy.

React Dashboard
       │
       │ /api/wells
       │ /api/analyze
       ▼
   Vite Proxy
       │
       ▼
   FastAPI
       │
       ▼
 NWIS AI Engine

Both servers should be running:

Backend

uvicorn backend.main:app --reload

Frontend

npm run dev

Then open:

http://localhost:5173

⸻

📊 Example End-to-End Operation

Select a target well from the dashboard.

For example:

Norway-Statoil-NO 15_$47$_9-F-9

Click:

Analyze

The system then performs:

1. Load target well
       ↓
2. Retrieve current drilling parameters
       ↓
3. Identify similar offset wells
       ↓
4. Calculate trajectory similarity
       ↓
5. Predict drilling risk
       ↓
6. Search historical drilling events
       ↓
7. Generate operational recommendations
       ↓
8. Display the results on the dashboard

⸻

📈 Current Prototype Results

The current prototype successfully demonstrates:

* WITSML XML parsing
* Well trajectory extraction
* Historical drilling-event extraction
* Event-depth mapping
* Drilling parameter extraction
* Temporal risk feature engineering
* Random Forest risk prediction
* Semantic historical-event retrieval
* FAISS vector search
* Recommendation generation
* End-to-end NWIS pipeline
* FastAPI API
* React dashboard

The prototype dataset currently contains three main Volve wells used for trajectory analysis:

Norway-Statoil-NO 15_$47$_9-F-4
Norway-Statoil-NO 15_$47$_9-F-7
Norway-Statoil-NO 15_$47$_9-F-9

⸻

⚠️ Data and Model Limitations

This project is currently an academic/research prototype.

The available public dataset contains a limited number of usable historical risk incidents. Therefore, the current machine-learning model should not be interpreted as a production-grade drilling-risk predictor.

The model requires:

* More historical wells
* More drilling incidents
* Better-balanced risk labels
* More complete drilling channels
* Domain-expert validation
* Real field-data testing

The current system should therefore be considered a decision-support prototype, not an autonomous drilling-control system.

⸻

🇮🇳 Oil India Deployment Context

The system architecture is designed to support future integration with real Oil India drilling data.

The current prototype does not use proprietary Oil India drilling data.

Instead:

Public WITSML Data
       ↓
Prototype Development
       ↓
eRTMAC-NWIS Architecture
       ↓
Future Oil India WITSML Integration

With access to appropriate historical and real-time field data, the same architecture can be extended for:

* Real-time drilling monitoring
* Historical offset-well analysis
* Risk prediction
* Event detection
* RAG-based drilling knowledge retrieval
* Decision-support recommendations

⸻

🔐 Production Deployment Considerations

For production deployment, the following components should be added:

* Authentication and authorization
* Secure API gateway
* Production database
* Real-time WITSML/ETP integration
* Data validation
* Model monitoring
* Model versioning
* Audit logging
* Role-based access control
* Secure infrastructure
* Continuous model evaluation
* Domain-expert approval workflows

⸻

🛠️ Troubleshooting

FastAPI cannot start

Make sure the terminal is in the project root:

eRTMAC-NWIS/

Then start:

uvicorn backend.main:app --reload

⸻

Frontend cannot connect to FastAPI

Make sure both services are running:

FastAPI  → http://127.0.0.1:8000
React    → http://localhost:5173

The frontend uses the Vite proxy to communicate with FastAPI.

⸻

No wells appear

Make sure the trajectory dataset has been generated:

data/processed/well_trajectories.csv

If missing, run the WITSML trajectory parser again.

⸻

RAG search does not work

Make sure the RAG index exists:

data/processed/rag/

If it does not exist, rebuild the index using the RAG indexing script.

⸻

Large dataset files

Some generated datasets can be very large.

Large processed files should not be committed directly to a standard Git repository.

For production or large-scale collaboration, use:

* Git LFS
* Cloud object storage
* Dataset repositories
* Database storage
* Data pipelines

⸻

🔮 Future Scope

The next development stages include:

Real-Time WITSML Integration

Connect the platform directly to live drilling data using WITSML/ETP.

3D Well Trajectory Visualization

Provide interactive 3D visualization of target and offset well trajectories.

Advanced Spatial Intelligence

Use real well coordinates when available to improve offset-well ranking.

Time-Series Risk Prediction

Use sequential drilling data instead of isolated feature windows.

Advanced Event Detection

Automatically detect:

* Kick
* Lost circulation
* Stuck pipe
* Pressure anomalies
* Gas influx
* Abnormal drilling behaviour

Advanced RAG Assistant

Introduce an LLM-powered drilling assistant capable of answering natural-language engineering questions using historical well knowledge.

Production Deployment

Integrate the system with enterprise drilling infrastructure and real-time monitoring systems.

⸻

🧩 Planned Architecture

                    REAL-TIME WITSML / ETP
                             │
                             ▼
                    Streaming Data Layer
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
     Trajectory         Parameters           Events
          │                  │                  │
          ▼                  ▼                  ▼
 Offset Intelligence    Time-Series ML       Event AI
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                      Knowledge Layer
                             │
                       RAG + Vector DB
                             │
                             ▼
                     Decision Engine
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
          Risk Score    Offset Wells    Recommendations
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                      eRTMAC-NWIS UI

⸻

📌 Project Status

Component	Status
WITSML Data Extraction	✅ Complete
Well Trajectory Processing	✅ Complete
Offset Trajectory Similarity	✅ Complete
Drilling Event Extraction	✅ Complete
Event Depth Mapping	✅ Complete
Drilling Parameter Extraction	✅ Complete
Risk Feature Engineering	✅ Complete
Random Forest Risk Model	✅ Complete
RAG Indexing	✅ Complete
FAISS Semantic Search	✅ Complete
Recommendation Engine	✅ Complete
NWIS AI Pipeline	✅ Complete
FastAPI Backend	✅ Complete
React Dashboard	✅ Complete
Neumorphic UI	✅ Complete
Advanced 3D Visualization	🔄 Planned
Real-Time WITSML/ETP	🔄 Planned
Production ML Validation	🔄 Planned
Oil India Field Integration	🔄 Future

⸻

👨‍💻 Project

eRTMAC-NWIS

Nearby Wells Intelligence System

AI-Powered Offset Well Knowledge and Decision Support Platform for Drilling Operations

An academic/research prototype combining WITSML, Machine Learning, RAG, FAISS, FastAPI and React to transform historical drilling data into intelligent decision-support information.

⸻

⚠️ Disclaimer

eRTMAC-NWIS is an academic/research prototype.

The system is intended to assist engineering analysis and knowledge retrieval. Its predictions and recommendations must not be treated as a replacement for qualified drilling engineers, well-control procedures, company operating standards, or safety-critical operational decision-making.
