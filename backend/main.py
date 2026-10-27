from backend import offset
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from backend.agents.orchestrator import build_agentic_trace
from backend.agents.agent_runtime import run_agentic_workflow

# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.append(str(BASE_DIR / "backend"))


# ============================================================
# AI MODULES
# ============================================================


from offset.trajectory_similarity import (
    rank_offset_wells,
    load_trajectories,
)

from ai.risk_predictor import train_model, predict_risk
from ai.recommendation_engine import generate_recommendation
from ai.rag_search import search_events
from ai.issue_detector import detect_issue_notification

from backend.data.sodir_service import (
    get_sodir_stats,
    search_sodir_wellbores,
    get_sodir_wellbore,
)
from backend.data.well_locations import normalize_well_name
from backend.offset.spatial import spatial_similarity


# ============================================================
# DATA FILES
# ============================================================

def resolve_data_file(subpath: str) -> Path:
    filename = Path(subpath).name
    candidates = [
        BASE_DIR / subpath,
        Path(__file__).resolve().parent / subpath,
        Path(__file__).resolve().parent / "data" / "processed" / filename,
        Path.cwd() / subpath,
        Path.cwd() / "data" / "processed" / filename,
        Path.cwd().parent / subpath,
        Path.cwd().parent / "data" / "processed" / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

RISK_FILE = resolve_data_file("data/processed/risk_features.csv")
TRAJECTORY_FILE = resolve_data_file("data/processed/well_trajectories.csv")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="eRTMAC-NWIS API",
    description=(
        "AI-Powered Offset Well Intelligence "
        "and Decision Support System"
    ),
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://tejas813.github.io",
    ],
    allow_origin_regex=r"^https:\/\/.*\.github\.io$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class AnalyzeRequest(BaseModel):
    well_id: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "system": "eRTMAC-NWIS",
        "status": "running",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# AVAILABLE WELLS
# ============================================================

DEFAULT_WELLS = [
    "Norway-Statoil-NO 15_$47$_9-F-4",
    "Norway-Statoil-NO 15_$47$_9-F-7",
    "Norway-Statoil-NO 15_$47$_9-F-9",
]


@app.get("/wells")
def get_wells():
    wells = []
    try:
        traj_file = resolve_data_file("data/processed/well_trajectories.csv")
        if traj_file.exists():
            trajectory_df = pd.read_csv(traj_file)
            wells = sorted(
                trajectory_df["well_id"]
                .dropna()
                .unique()
                .tolist()
            )
    except Exception as exc:
        print(f"Warning: Failed reading trajectory file: {exc}")

    if not wells:
        wells = DEFAULT_WELLS

    return {
        "count": len(wells),
        "wells": wells
    }


# ============================================================
# ANALYZE WELL
# ============================================================

@app.post("/analyze")
def analyze_well(request: AnalyzeRequest):

    well_id = request.well_id

    # --------------------------------------------------------
    # LOAD RISK DATA
    # --------------------------------------------------------

    if not RISK_FILE.exists():

        raise HTTPException(
            status_code=500,
            detail="Risk feature data not found."
        )

    risk_df = pd.read_csv(
        RISK_FILE
    )

    well_data = risk_df[
        risk_df["well_id"] == well_id
    ].copy()

    if well_data.empty:

        raise HTTPException(
            status_code=404,
            detail=f"No risk data found for well: {well_id}"
        )

    # Latest available drilling condition
    current = well_data.iloc[-1]

    # --------------------------------------------------------
    # CURRENT DRILLING CONDITION
    # --------------------------------------------------------

    current_condition = {

        "depth": float(
            current["Depth"]
        ),

        "wob": float(
            current["WOB"]
        ),

        "torque": float(
            current["TORQUE"]
        ),

        "flow_in": float(
            current["FLOWIN"]
        ),

        "flow_out": float(
            current["FLOWOUT"]
        ),

        "pump": float(
            current["PUMP"]
        )
    }

    # --------------------------------------------------------
    # OFFSET WELL INTELLIGENCE & SODIR SPATIAL ENRICHMENT
    # --------------------------------------------------------

    # Resolve target well SODIR metadata & coordinates
    target_sodir = get_sodir_wellbore(well_id)
    target_lat = target_sodir.get("latitude") if target_sodir else None
    target_lon = target_sodir.get("longitude") if target_sodir else None

    # Load trajectory stations grouped by well ID.
    wells = load_trajectories()

    print("DEBUG trajectory wells type:", type(wells).__name__)
    print("DEBUG trajectory well IDs:", list(wells.keys()))

    offsets = []

    try:
        if well_id not in wells:
            raise ValueError(
                f"Target well {well_id!r} not found in trajectory data"
            )

        offset_results = rank_offset_wells(
            target_well=well_id,
            wells=wells,
            top_k=5,
        )

        print("DEBUG offset results:", offset_results)

        for result in offset_results:
            off_id = result["offset_well"]
            off_sodir = get_sodir_wellbore(off_id)
            off_lat = off_sodir.get("latitude") if off_sodir else None
            off_lon = off_sodir.get("longitude") if off_sodir else None

            spatial = spatial_similarity(
                target_lat,
                target_lon,
                off_lat,
                off_lon,
            )
            spatial_score = spatial.get("score")
            distance_km = spatial.get("distance_km")

            traj_score = float(result["similarity_score"])
            target_max_md = float(result["target_max_md"])
            offset_max_md = float(result["offset_max_md"])
            depth_diff = float(result["depth_difference"])

            depth_score = 1.0 / (
                1.0 + depth_diff / max(target_max_md, 1.0)
            )

            if spatial_score is not None:
                master_score = (
                    0.50 * traj_score
                    + 0.20 * depth_score
                    + 0.30 * spatial_score
                )
            else:
                master_score = 0.70 * traj_score + 0.30 * depth_score

            offsets.append({
                "well_id": off_id,
                "sodir_name": off_sodir.get("wellbore_name") if off_sodir else normalize_well_name(off_id),
                "similarity_score": traj_score,
                "trajectory_score": round(traj_score, 4),
                "depth_score": round(depth_score, 4),
                "spatial_score": spatial_score,
                "distance_km": distance_km,
                "master_score": round(master_score, 4),
                "target_max_md": target_max_md,
                "offset_max_md": offset_max_md,
                "depth_difference": depth_diff,
                "latitude": off_lat,
                "longitude": off_lon,
                "field": off_sodir.get("field") if off_sodir else None,
                "operator": off_sodir.get("operator") if off_sodir else None,
                "purpose": off_sodir.get("purpose") if off_sodir else None,
            })

    except Exception as e:
        import traceback
        print("Offset ranking error:", repr(e))
        traceback.print_exc()
        offsets = []



   
         

    # --------------------------------------------------------
    # RISK PREDICTION
    # --------------------------------------------------------

    try:

        model = train_model()

        features = [

            "Depth",
            "BITDEP",
            "VDEPTH",
            "WOB",
            "TORQUE",
            "TQ_IN_AMPS",
            "TQ_IN_AMPS_AV",
            "FLOWIN",
            "FLOWOUT",
            "MWIN",
            "MWOUT",
            "ECDCS",
            "PUMP",
            "PUMPPOWER"

        ]

        sample = {}

        for feature in features:

            sample[feature] = current.get(
                feature,
                np.nan
            )

        probability, risk_level = (
            predict_risk(
                model,
                sample
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction failed: {str(e)}"
        )

    # --------------------------------------------------------
    # HISTORICAL RAG INTELLIGENCE
    # --------------------------------------------------------

    query = (

        f"drilling operation at depth "
        f"{current['Depth']:.0f} m "

        f"with WOB "
        f"{current['WOB']:.2f}, "

        f"torque "
        f"{current['TORQUE']:.2f}, "

        f"flow changes and pump activity"

    )

    try:

        rag_results = search_events(
            query,
            top_k=5
        )

    except Exception as e:

        print(
            f"RAG search error: {e}"
        )

        rag_results = []

    historical_events = []

    for result in rag_results:

        historical_events.append({

            "similarity_score": float(
                result[
                    "similarity_score"
                ]
            ),

            "well_id": result[
                "well_id"
            ],

            "event_type": result[
                "event_type"
            ],

            "depth": float(
                result[
                    "event_md"
                ]
            ),

            "timestamp": result[
                "timestamp"
            ],

            "description": result[
                "description"
            ]

        })

    # --------------------------------------------------------
    # DETERMINE EVENT TYPE
    # --------------------------------------------------------

    event_type = None

    if historical_events:

        top_event = historical_events[0][
            "event_type"
        ]

        if top_event in [

            "pressure_event",
            "gas_event",
            "well_control",
            "stuck_pipe",
            "lost_circulation"

        ]:

            event_type = top_event

    # --------------------------------------------------------
    # RECOMMENDATION ENGINE
    # --------------------------------------------------------

    recommendations = generate_recommendation(

        risk_probability=probability,

        risk_level=risk_level,

        event_type=event_type,

        depth=current["Depth"]

    )

    # --------------------------------------------------------
    # FINAL API RESPONSE
    # --------------------------------------------------------

    response = {
        "system": "eRTMAC-NWIS",
        "target_well": well_id,
        "sodir_metadata": target_sodir,
        "sodir_verified": bool(target_sodir and target_sodir.get("latitude") is not None),
        "current_condition": current_condition,
        "risk": {
            "probability": float(probability),
            "level": risk_level,
        },
        "offset_wells": offsets,
        "historical_events": historical_events,
        "recommendations": recommendations,
        "status": "complete",
    }

    try:
        response["issue_notification"] = detect_issue_notification(response)
    except Exception as e:
        print(f"Issue notification detection error: {e}")
        response["issue_notification"] = None

    return response



@app.post("/agentic-analyze")
def agentic_analyze(request: AnalyzeRequest):
    analysis = analyze_well(request)

    def retry_historical_search():
        """Retry RAG once with a broader query if initial evidence is empty."""
        condition = analysis.get("current_condition") or {}

        depth = condition.get("depth")
        wob = condition.get("wob")
        torque = condition.get("torque")

        query_parts = [
            "historical drilling incidents and abnormal drilling conditions"
        ]

        if depth is not None:
            query_parts.append(f"depth {depth} m")
        if wob is not None:
            query_parts.append(f"weight on bit {wob}")
        if torque is not None:
            query_parts.append(f"torque {torque}")

        retry_query = " ".join(query_parts)

        try:
            results = search_events(retry_query, top_k=5)
            events = []

            for result in results or []:
                events.append({
                    "similarity_score": float(
                        result.get("similarity_score", 0.0)
                    ),
                    "well_id": result.get("well_id"),
                    "event_type": result.get("event_type"),
                    "depth": result.get("event_md"),
                    "timestamp": result.get("timestamp"),
                })

            return {
                "attempted": True,
                "query": retry_query,
                "result_count": len(events),
                "events": events,
                "status": "results_found" if events else "no_results",
            }

        except Exception as exc:
            # Keep the API available and record the failure for diagnosis.
            print(f"Agentic RAG retry error: {exc}")
            return {
                "attempted": True,
                "query": retry_query,
                "result_count": 0,
                "events": [],
                "status": "error",
                "error": str(exc),
            }

    retry_result = None

    if not analysis.get("historical_events"):
        retry_result = retry_historical_search()

        if retry_result["events"]:
            analysis["historical_events"] = retry_result["events"]

    agentic = run_agentic_workflow(analysis)

    agentic["retrieval_retry"] = (
        retry_result
        if retry_result is not None
        else {
            "attempted": False,
            "status": "not_needed",
            "reason": "Initial analysis already returned historical events.",
        }
    )

    analysis["agentic"] = agentic
    if agentic.get("issue_notification"):
        analysis["issue_notification"] = agentic["issue_notification"]
    return analysis


# ============================================================
# OFFICIAL SODIR DATASET ENDPOINTS
# ============================================================

@app.get("/sodir/stats")
def sodir_stats():
    """
    Get summary statistics for the official Norwegian Offshore Directorate
    (SODIR) FactMaps wellbore point layer dataset (9,869 records).
    """
    try:
        return get_sodir_stats()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load SODIR dataset statistics: {exc}"
        )


@app.get("/sodir/wellbores")
def list_sodir_wellbores(
    search: str = None,
    field: str = None,
    operator: str = None,
    purpose: str = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Query the official SODIR wellbores layer with search filters and pagination.
    """
    try:
        return search_sodir_wellbores(
            search=search,
            field=field,
            operator=operator,
            purpose=purpose,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query SODIR wellbores: {exc}"
        )


@app.get("/sodir/wellbores/{wellbore_name:path}")
def get_single_sodir_wellbore(wellbore_name: str):
    """
    Retrieve full official metadata and WGS84 coordinates for a specific wellbore.
    """
    try:
        wb = get_sodir_wellbore(wellbore_name)
        if not wb:
            raise HTTPException(
                status_code=404,
                detail=f"Wellbore '{wellbore_name}' not found in official SODIR registry."
            )
        return wb
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve wellbore '{wellbore_name}': {exc}"
        )


