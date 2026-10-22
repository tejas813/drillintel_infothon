import pandas as pd
import numpy as np
import sys
from pathlib import Path

# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Allow importing backend modules
sys.path.append(str(BASE_DIR / "backend"))

from offset.trajectory_similarity import rank_offset_wells
from ai.risk_predictor import train_model, predict_risk
from ai.recommendation_engine import generate_recommendation
from ai.rag_search import search_events


# ============================================================
# DATA FILES
# ============================================================

RISK_FILE = BASE_DIR / "data/processed/risk_features.csv"

TRAJECTORY_FILE = (
    BASE_DIR / "data/processed/well_trajectories.csv"
)


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline(well_id):

    print("=" * 80)
    print(
        "eRTMAC-NWIS | NEARBY WELLS INTELLIGENCE "
        "& DECISION ENGINE"
    )
    print("=" * 80)

    print(f"\nTarget Well: {well_id}")

    # ========================================================
    # 1. LOAD RISK DATA
    # ========================================================

    df = pd.read_csv(RISK_FILE)

    well_data = df[
        df["well_id"] == well_id
    ].copy()

    if well_data.empty:

        print(
            "\nNo risk data found for target well."
        )

        return

    # Latest available condition
    current = well_data.iloc[-1]

    print("\n" + "-" * 80)
    print("CURRENT DRILLING CONDITION")
    print("-" * 80)

    print(
        f"Depth   : {current['Depth']:.2f} m"
    )

    print(
        f"WOB     : {current['WOB']:.2f}"
    )

    print(
        f"Torque  : {current['TORQUE']:.2f}"
    )

    print(
        f"Flow In : {current['FLOWIN']:.6f}"
    )

    print(
        f"Flow Out: {current['FLOWOUT']:.6f}"
    )

    print(
        f"Pump    : {current['PUMP']:.2f}"
    )

    # ========================================================
    # 2. OFFSET WELL INTELLIGENCE
    # ========================================================

    print("\n" + "-" * 80)
    print("OFFSET WELL INTELLIGENCE")
    print("-" * 80)

    trajectory_df = pd.read_csv(
        TRAJECTORY_FILE
    )

    wells = sorted(
        trajectory_df["well_id"]
        .dropna()
        .unique()
        .tolist()
    )

    offset_results = []

    try:

        offset_results = rank_offset_wells(
            target_well=well_id,
            wells=wells,
            top_k=5
        )

        if not offset_results:

            print(
                "No offset wells found."
            )

        else:

            for i, result in enumerate(
                offset_results,
                start=1
            ):

                print(
                    f"\n{i}. Offset Well:"
                    f" {result['offset_well']}"
                )

                print(
                    f"   Trajectory Similarity : "
                    f"{result['similarity_score'] * 100:.2f}%"
                )

                print(
                    f"   Target Max MD         : "
                    f"{result['target_max_md']:.2f} m"
                )

                print(
                    f"   Offset Max MD         : "
                    f"{result['offset_max_md']:.2f} m"
                )

                print(
                    f"   Depth Difference      : "
                    f"{result['depth_difference']:.2f} m"
                )

    except Exception as e:

        print(
            f"Offset ranking unavailable: {e}"
        )

        offset_results = []

    # ========================================================
    # 3. RISK PREDICTION
    # ========================================================

    print("\n" + "-" * 80)
    print("RISK PREDICTION")
    print("-" * 80)

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

        "PUMPPOWER",

    ]

    sample = {}

    for feature in features:

        sample[feature] = current.get(
            feature,
            np.nan
        )

    probability, risk_level = predict_risk(
        model,
        sample
    )

    print(
        f"\nRisk Probability : "
        f"{probability:.2f}%"
    )

    print(
        f"Risk Level       : "
        f"{risk_level}"
    )

    # ========================================================
    # 4. HISTORICAL RAG INTELLIGENCE
    # ========================================================

    print("\n" + "-" * 80)
    print("HISTORICAL RAG INTELLIGENCE")
    print("-" * 80)

    query = (
        f"drilling operation at depth "
        f"{current['Depth']:.0f} m "
        f"with WOB {current['WOB']:.2f}, "
        f"torque {current['TORQUE']:.2f}, "
        f"flow changes and pump activity"
    )

    print(
        f"\nRAG Query:\n{query}"
    )

    rag_results = []

    try:

        rag_results = search_events(
            query,
            top_k=5
        )

        if not rag_results:

            print(
                "No historical matches found."
            )

        else:

            for i, result in enumerate(
                rag_results,
                start=1
            ):

                print(
                    "\n" + "." * 70
                )

                print(
                    f"Historical Match #{i}"
                )

                print(
                    f"Similarity : "
                    f"{result['similarity_score']:.4f}"
                )

                print(
                    f"Well       : "
                    f"{result['well_id']}"
                )

                print(
                    f"Event      : "
                    f"{result['event_type']}"
                )

                print(
                    f"Depth      : "
                    f"{result['event_md']} m"
                )

                print(
                    f"Timestamp  : "
                    f"{result['timestamp']}"
                )

                print(
                    f"Description: "
                    f"{result['description']}"
                )

    except Exception as e:

        print(
            f"RAG search unavailable: {e}"
        )

        rag_results = []

    # ========================================================
    # 5. DETERMINE HISTORICAL EVENT TYPE
    # ========================================================

    event_type = None

    if rag_results:

        top_event = (
            rag_results[0]
            .get("event_type")
        )

        if top_event in [

            "pressure_event",

            "gas_event",

            "well_control",

            "stuck_pipe",

            "lost_circulation",

        ]:

            event_type = top_event

    # ========================================================
    # 6. RECOMMENDATION ENGINE
    # ========================================================

    print("\n" + "-" * 80)
    print("NWIS RECOMMENDATION")
    print("-" * 80)

    recommendations = generate_recommendation(

        risk_probability=probability,

        risk_level=risk_level,

        event_type=event_type,

        depth=current["Depth"],

    )

    for i, recommendation in enumerate(

        recommendations,

        start=1

    ):

        print(
            f"{i}. {recommendation}"
        )

    # ========================================================
    # 7. FINAL NWIS DECISION
    # ========================================================

    print("\n" + "=" * 80)
    print("FINAL NWIS DECISION")
    print("=" * 80)

    print(
        f"\nTarget Well      : {well_id}"
    )

    print(
        f"Current Depth    : "
        f"{current['Depth']:.2f} m"
    )

    print(
        f"Risk Probability : "
        f"{probability:.2f}%"
    )

    print(
        f"Risk Level       : "
        f"{risk_level}"
    )

    # Best offset well
    if offset_results:

        best_offset = offset_results[0]

        print(
            f"Best Offset Well : "
            f"{best_offset['offset_well']}"
        )

        print(
            f"Offset Similarity: "
            f"{best_offset['similarity_score'] * 100:.2f}%"
        )

        print(
            f"Depth Difference : "
            f"{best_offset['depth_difference']:.2f} m"
        )

    else:

        print(
            "Best Offset Well : N/A"
        )

    # Top historical event
    if rag_results:

        top_result = rag_results[0]

        print(
            f"Top Historical Event : "
            f"{top_result['event_type']}"
        )

        print(
            f"Historical Similarity : "
            f"{top_result['similarity_score']:.4f}"
        )

        print(
            f"Historical Well       : "
            f"{top_result['well_id']}"
        )

    else:

        print(
            "Top Historical Event : N/A"
        )

    print(
        "\nDecision Support Status: COMPLETE"
    )

    print("=" * 80)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    target_well = (
        "Norway-Statoil-NO 15_$47$_9-F-9"
    )

    run_pipeline(
        target_well
    )
