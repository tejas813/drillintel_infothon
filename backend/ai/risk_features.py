import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

PARAM_FILE = BASE_DIR / "data/processed/drilling_parameters.csv"
EVENT_FILE = BASE_DIR / "data/processed/drilling_events_with_depth.csv"
OUTPUT_FILE = BASE_DIR / "data/processed/risk_features.csv"

RISK_EVENTS = {
    "well_control",
    "stuck_pipe",
    "lost_circulation",
    "pressure_event",
    "gas_event",
}

FEATURES = [
    "Depth", "BITDEP", "VDEPTH", "WOB", "RPM", "ROP", "TORQUE", "TQ",
    "TQ_IN_AMPS", "TQ_IN_AMPS_AV", "FLOWIN", "FLOWOUT", "FLOWOUTPC",
    "MWIN", "MWOUT", "MWINANN", "MWDLOSS", "ECDCS", "ECDBIT", "PUMP",
    "PUMPPOWER", "BITPOWER", "JETVEL", "BITLOSS", "DSTRINGLOSS",
    "MOTORLOSS", "SURFLOSS", "IMPACT", "HCCI",
]


def aggregate_window(window):
    if window.empty:
        return None

    row = {}

    for col in FEATURES:
        if col not in window.columns:
            continue

        values = pd.to_numeric(
            window[col], errors="coerce"
        ).dropna()

        row[col] = values.median() if not values.empty else np.nan

    row["source_file"] = (
        window["source_file"].dropna().iloc[0]
        if "source_file" in window.columns
        and window["source_file"].notna().any()
        else ""
    )

    row["Time"] = window["Time"].max()
    row["window_rows"] = int(len(window))

    return row


def main():

    print("=" * 80)
    print("eRTMAC-NWIS | TEMPORAL RISK FEATURE ENGINEERING")
    print("=" * 80)

    drilling = pd.read_csv(PARAM_FILE)
    events = pd.read_csv(EVENT_FILE)

    print("\nDrilling rows :", len(drilling))
    print("Event rows    :", len(events))

    drilling["Time"] = pd.to_datetime(
        drilling["Time"],
        errors="coerce",
        utc=True
    )

    drilling["Depth"] = pd.to_numeric(
        drilling["Depth"],
        errors="coerce"
    )

    events["timestamp"] = pd.to_datetime(
        events["timestamp"],
        errors="coerce",
        utc=True
    )

    events["event_md"] = pd.to_numeric(
        events["event_md"],
        errors="coerce"
    )

    risk_events = events[
        events["event_type"]
        .astype(str)
        .str.lower()
        .isin(RISK_EVENTS)
    ].copy()

    risk_events = risk_events.dropna(
        subset=["well_id", "event_md", "timestamp"]
    )

    print(
        "\nRisk events with usable time/depth:",
        len(risk_events)
    )

    # Each different timestamp is a separate incident.
    unique_events = (
        risk_events
        .assign(
            event_type=risk_events["event_type"]
            .astype(str)
            .str.lower()
        )
        .groupby(
            ["well_id", "event_md", "timestamp"],
            as_index=False
        )
        .agg(
            event_type=(
                "event_type",
                lambda x: "+".join(sorted(set(x)))
            )
        )
    )

    print(
        "Unique timestamped risk incidents:",
        len(unique_events)
    )

    print("\nRisk incident list:")

    if not unique_events.empty:
        print(unique_events.to_string(index=False))

    # ---------------------------------------------------------
    # POSITIVE EVENT WINDOWS
    # ---------------------------------------------------------

    positive_rows = []

    for _, event in unique_events.iterrows():

        well_id = event["well_id"]
        event_time = event["timestamp"]
        event_md = event["event_md"]

        well_data = drilling[
            drilling["well_id"] == well_id
        ].dropna(
            subset=["Time"]
        ).copy()

        if well_data.empty:
            continue

        start_time = (
            event_time
            - pd.Timedelta(minutes=5)
        )

        window = well_data[
            (well_data["Time"] >= start_time)
            &
            (well_data["Time"] < event_time)
        ].copy()

        if window.empty:
            continue

        row = aggregate_window(window)

        if row is None:
            continue

        row["well_id"] = well_id
        row["event_type"] = event["event_type"]
        row["event_md"] = event_md
        row["event_timestamp"] = event_time

        if pd.notna(row.get("Depth")):
            row["md_difference"] = abs(
                row["Depth"] - event_md
            )
        else:
            row["md_difference"] = np.nan

        row["risk_label"] = 1
        row["sample_type"] = "risk_event"

        positive_rows.append(row)

    positive = pd.DataFrame(positive_rows)

    print(
        "\nPositive event windows:",
        len(positive)
    )

    # ---------------------------------------------------------
    # NORMAL WINDOWS
    # ---------------------------------------------------------

    normal_rows = []

    rng = np.random.default_rng(42)

    for well_id, well_data in drilling.groupby(
        "well_id"
    ):

        well_data = (
            well_data
            .dropna(subset=["Time"])
            .sort_values("Time")
            .copy()
        )

        if well_data.empty:
            continue

        event_times = unique_events.loc[
            unique_events["well_id"] == well_id,
            "timestamp"
        ].tolist()

        candidate_times = (
            well_data["Time"]
            .drop_duplicates()
            .tolist()
        )

        safe_times = []

        for t in candidate_times:

            too_close = any(
                abs(t - event_time)
                <= pd.Timedelta(minutes=15)
                for event_time in event_times
            )

            if not too_close:
                safe_times.append(t)

        if not safe_times:
            continue

        target = max(
            20,
            len(positive) * 3
        )

        n = min(
            len(safe_times),
            target
        )

        selected = rng.choice(
            len(safe_times),
            size=n,
            replace=False
        )

        for index in selected:

            end_time = safe_times[index]

            start_time = (
                end_time
                - pd.Timedelta(minutes=5)
            )

            window = well_data[
                (well_data["Time"] >= start_time)
                &
                (well_data["Time"] <= end_time)
            ].copy()

            if window.empty:
                continue

            row = aggregate_window(window)

            if row is None:
                continue

            row["well_id"] = well_id
            row["event_type"] = "normal"
            row["event_md"] = np.nan
            row["event_timestamp"] = pd.NaT
            row["md_difference"] = np.nan
            row["risk_label"] = 0
            row["sample_type"] = "normal_drilling"

            normal_rows.append(row)

    normal = (
        pd.DataFrame(normal_rows)
        if normal_rows
        else pd.DataFrame()
    )

    print(
        "Normal windows:",
        len(normal)
    )

    # ---------------------------------------------------------
    # COMBINE
    # ---------------------------------------------------------

    result = pd.concat(
        [positive, normal],
        ignore_index=True
    )

    before = len(result)

    result = result.drop_duplicates()

    print(
        "\nRemoved duplicate rows:",
        before - len(result)
    )

    base_columns = [
        "well_id",
        "source_file",
        "Time",
        "Depth",
        "event_type",
        "event_md",
        "event_timestamp",
        "md_difference",
        "window_rows",
        "risk_label",
        "sample_type",
    ]

    available_features = [
        col for col in FEATURES
        if col in result.columns
        and col != "Depth"
    ]

    output_columns = list(
        dict.fromkeys(
            base_columns + available_features
        )
    )

    result = result[
        [
            col for col in output_columns
            if col in result.columns
        ]
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ---------------------------------------------------------
    # FINAL REPORT
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("TEMPORAL RISK DATASET COMPLETE")
    print("=" * 80)

    print("\nOutput file:")
    print(OUTPUT_FILE)

    print("\nTotal samples:")
    print(len(result))

    print("\nRisk labels:")
    print(
        result["risk_label"]
        .value_counts()
        .sort_index()
    )

    print("\nSample types:")
    print(
        result["sample_type"]
        .value_counts()
    )

    print("\nRisk incidents:")

    positive_display = result[
        result["risk_label"] == 1
    ][
        [
            "well_id",
            "event_type",
            "event_md",
            "Depth",
            "event_timestamp",
            "window_rows",
        ]
    ]

    if positive_display.empty:
        print("No positive windows created.")
    else:
        print(
            positive_display.to_string(
                index=False
            )
        )

    print("\nFeature availability:")

    for col in available_features:

        count = int(
            result[col].notna().sum()
        )

        print(
            f"{col:<18} {count:6d} values"
        )

    print("\nSaved successfully.")


if __name__ == "__main__":
    main()
