import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


EVENT_FILE = Path("data/processed/drilling_events.csv")
TRAJECTORY_FILE = Path("data/processed/well_trajectories.csv")
OUTPUT_FILE = Path("data/processed/drilling_events_with_depth.csv")


def lname(tag):
    return tag.split("}")[-1].lower()


def clean_number(value):
    if value is None:
        return None

    try:
        value = str(value).strip()

        if not value:
            return None

        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return None

        return number

    except (ValueError, TypeError):
        return None


def extract_md_from_xml(source_file):
    """
    Read actual measured depth from the original WITSML event XML.
    """

    if not source_file:
        return None

    path = Path(source_file)

    if not path.exists():
        return None

    try:
        root = ET.parse(path).getroot()
    except Exception:
        return None

    # Look for md directly in the event/message XML
    for elem in root.iter():

        if lname(elem.tag) == "md":

            value = clean_number(elem.text)

            if value is not None:
                return value

    return None


def find_nearest_trajectory(trajectory, well_id, event_md):

    if event_md is None:
        return None, None, False

    well_data = trajectory[
        trajectory["well_id"].astype(str) == str(well_id)
    ].copy()

    if well_data.empty:
        return None, None, False

    well_data["md"] = pd.to_numeric(
        well_data["md"],
        errors="coerce"
    )

    well_data = well_data.dropna(subset=["md"])

    if well_data.empty:
        return None, None, False

    differences = (
        well_data["md"] - event_md
    ).abs()

    idx = differences.idxmin()

    nearest_md = float(
        well_data.loc[idx, "md"]
    )

    difference = abs(
        nearest_md - event_md
    )

    return nearest_md, difference, True


def main():

    print("=" * 80)
    print("eRTMAC-NWIS | EVENT → TRAJECTORY DEPTH MAPPING")
    print("=" * 80)

    events = pd.read_csv(EVENT_FILE)
    trajectory = pd.read_csv(TRAJECTORY_FILE)

    print(f"\nEvents loaded: {len(events)}")
    print(f"Trajectory rows: {len(trajectory)}")

    # Ensure required columns exist
    if "event_md" not in events.columns:
        events["event_md"] = None

    # ---------------------------------------------------------
    # Re-read MD directly from source XML
    # ---------------------------------------------------------

    recovered = 0

    for i in events.index:

        current_md = clean_number(
            events.at[i, "event_md"]
        )

        if current_md is not None:
            continue

        source_file = events.at[i, "source_file"]

        xml_md = extract_md_from_xml(
            source_file
        )

        if xml_md is not None:
            events.at[i, "event_md"] = xml_md
            recovered += 1

    print(
        f"\nMD values recovered directly from XML: {recovered}"
    )

    # ---------------------------------------------------------
    # Map event depth to nearest trajectory station
    # ---------------------------------------------------------

    nearest_values = []
    difference_values = []
    available_values = []

    mapped = 0
    unmapped = 0

    for _, row in events.iterrows():

        well_id = row["well_id"]
        event_md = clean_number(row["event_md"])

        nearest_md, difference, available = (
            find_nearest_trajectory(
                trajectory,
                well_id,
                event_md
            )
        )

        nearest_values.append(nearest_md)
        difference_values.append(difference)
        available_values.append(available)

        if available:
            mapped += 1
        else:
            unmapped += 1

    events["nearest_trajectory_md"] = nearest_values
    events["md_difference"] = difference_values
    events["trajectory_available"] = available_values

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "well_id",
        "event_type",
        "event_name",
        "timestamp",
        "description",
        "source_file",
        "event_md",
        "nearest_trajectory_md",
        "md_difference",
        "trajectory_available",
    ]

    # Make sure all columns exist
    for column in columns:
        if column not in events.columns:
            events[column] = None

    events[columns].to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("DEPTH MAPPING COMPLETE")
    print("=" * 80)

    print(f"Output: {OUTPUT_FILE}")
    print(f"Mapped events: {mapped}")
    print(f"Unmapped events: {unmapped}")

    print(
        f"Events with MD: "
        f"{events['event_md'].notna().sum()}"
    )

    print("\nEvents with recovered depth:")

    depth_events = events[
        events["event_md"].notna()
    ][
        [
            "well_id",
            "event_type",
            "event_name",
            "event_md",
            "nearest_trajectory_md",
            "md_difference",
            "trajectory_available",
        ]
    ]

    if depth_events.empty:
        print("NONE")
    else:
        print(
            depth_events.to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()
