import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import re


WITSML_DIR = Path("data/external/volve-drilling/witsml")
OUTPUT_FILE = Path("data/processed/drilling_events.csv")


def local_name(tag):
    """Remove XML namespace from tag."""
    return tag.split("}")[-1].lower()


def get_well_id(xml_file):
    """Extract well ID from folder structure."""
    parts = xml_file.parts

    try:
        idx = parts.index("witsml")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return xml_file.parent.parent.name


def classify_event(text):
    """Simple prototype event classification."""
    text = text.lower()

    if any(x in text for x in ["kick", "well control", "wellcontrol"]):
        return "well_control"

    if any(x in text for x in ["lost circulation", "losses", "loss of circulation"]):
        return "lost_circulation"

    if any(x in text for x in ["stuck pipe", "stuck"]):
        return "stuck_pipe"

    if any(x in text for x in ["pressure", "high pressure"]):
        return "pressure_event"

    if any(x in text for x in ["gas", "gas show"]):
        return "gas_event"

    return "drilling_event"


def extract_events(xml_file):
    """Extract drilling events/messages from one WITSML XML file."""

    events = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Could not parse {xml_file}: {e}")
        return events

    well_id = get_well_id(xml_file)

    # Find all message/event-like elements
    for element in root.iter():

        tag = local_name(element.tag)

        if tag not in [
            "message",
            "event",
            "wellcontrol",
            "wellcontrolitem"
        ]:
            continue

        values = {}

        for child in element.iter():
            child_tag = local_name(child.tag)

            if child.text and child.text.strip():
                values[child_tag] = child.text.strip()

        # Message/event text
        description = (
            values.get("messagetext")
            or values.get("description")
            or values.get("text")
            or values.get("name")
            or ""
        )

        # Event timestamp
        timestamp = (
            values.get("dtim")
            or values.get("timestamp")
            or values.get("datetime")
            or values.get("dtimcreation")
            or ""
        )

        # Actual measured depth
        event_md = (
            values.get("md")
            or values.get("measureddepth")
            or values.get("depth")
            or values.get("bitdepth")
            or values.get("holedepth")
            or ""
        )

        # Convert MD to numeric when possible
        try:
            event_md = float(event_md)
        except (ValueError, TypeError):
            event_md = None

        if not description:
            continue

        event_type = classify_event(description)

        events.append({
            "well_id": well_id,
            "source_file": str(xml_file),
            "event_type": event_type,
            "event_name": values.get("name", ""),
            "description": description,
            "timestamp": timestamp,
            "event_md": event_md
        })

    return events


def main():

    all_events = []

    xml_files = list(WITSML_DIR.rglob("*.xml"))

    print(f"XML files found: {len(xml_files)}")

    for xml_file in xml_files:
        events = extract_events(xml_file)
        all_events.extend(events)

    if not all_events:
        print("No drilling events found.")
        return

    df = pd.DataFrame(all_events)

    # Remove duplicate records
    df = df.drop_duplicates(
        subset=[
            "well_id",
            "event_type",
            "description",
            "timestamp",
            "event_md"
        ]
    )

    # Sort
    df = df.sort_values(
        by=["well_id", "timestamp"],
        na_position="last"
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\n===================================")
    print("DRILLING EVENT EXTRACTION COMPLETE")
    print("===================================")

    print(f"Total events: {len(df)}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nEvent distribution:")
    print(df["event_type"].value_counts())

    print("\nEvents by well:")
    print(df.groupby("well_id").size())

    print("\nEvents with measured depth:")
    print(df[df["event_md"].notna()][
        ["well_id", "event_type", "event_name", "event_md", "timestamp", "description"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
