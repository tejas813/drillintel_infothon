import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path


WITSML_DIR = Path("data/external/volve-drilling/witsml")
OUTPUT_FILE = Path("data/processed/drilling_parameters.csv")


CHANNELS = [
    "Time",
    "Depth",
    "BITDEP",
    "VBITSDEP",
    "VDEPTH",
    "WOB",
    "RPM",
    "ROP",
    "TORQUE",
    "TQ",
    "TQ_IN_AMPS",
    "TQ_IN_AMPS_AV",
    "FLOWIN",
    "FLOWOUT",
    "FLOWOUTPC",
    "MWIN",
    "MWOUT",
    "MWINANN",
    "MWDLOSS",
    "ECDCS",
    "ECDBIT",
    "PUMP",
    "PUMPPOWER",
    "BITPOWER",
    "JETVEL",
    "BITLOSS",
    "DSTRINGLOSS",
    "MOTORLOSS",
    "SURFLOSS",
    "IMPACT",
    "HCCI",
    "RigActivityCode",
    "EditFlag",
]


def lname(tag):
    return tag.split("}")[-1].lower()


def get_well_id(xml_file):
    parts = xml_file.parts

    try:
        idx = parts.index("witsml")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return xml_file.parent.name


def clean_number(value):
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return None

        return number

    except (ValueError, TypeError):
        return None


def get_mnemonic_list(log_element):
    """
    Get the ACTUAL data-column order from mnemonicList.
    """

    for elem in log_element.iter():

        if lname(elem.tag) == "mnemoniclist":

            if elem.text:
                text = elem.text.strip()

                mnemonics = [
                    x.strip()
                    for x in text.split(",")
                    if x.strip()
                ]

                if mnemonics:
                    return mnemonics

    return []


def extract_log_file(xml_file):

    rows = []

    try:
        root = ET.parse(xml_file).getroot()
    except Exception as e:
        print(f"ERROR parsing {xml_file}: {e}")
        return rows

    well_id = get_well_id(xml_file)

    # Find <log>
    log_element = None

    for elem in root.iter():

        if lname(elem.tag) == "log":
            log_element = elem
            break

    if log_element is None:
        return rows

    # ---------------------------------------------------------
    # IMPORTANT:
    # Use mnemonicList, NOT logCurveInfo order.
    # ---------------------------------------------------------

    mnemonics = get_mnemonic_list(log_element)

    if not mnemonics:
        print(f"WARNING: No mnemonicList in {xml_file}")
        return rows

    # Create index map
    channel_index = {
        name: i
        for i, name in enumerate(mnemonics)
    }

    # Find all <data> elements
    data_elements = []

    for elem in log_element.iter():

        if lname(elem.tag) == "data":

            if elem.text and elem.text.strip():
                data_elements.append(elem.text.strip())

    # ---------------------------------------------------------
    # Parse rows
    # ---------------------------------------------------------

    for data_text in data_elements:

        values = [
            x.strip()
            for x in data_text.split(",")
        ]

        row = {
            "well_id": well_id,
            "source_file": str(xml_file),
        }

        for channel in CHANNELS:

            idx = channel_index.get(channel)

            if idx is None:
                row[channel] = None
                continue

            if idx >= len(values):
                row[channel] = None
                continue

            value = values[idx]

            # Time is NOT numeric
            if channel == "Time":
                row[channel] = value if value else None

            elif channel in channel_index:
                row[channel] = clean_number(value)

        # Keep rows that contain at least timestamp
        if row.get("Time") is not None:
            rows.append(row)

    return rows


def main():

    print("=" * 80)
    print("eRTMAC-NWIS | WITSML DRILLING PARAMETER EXTRACTION")
    print("=" * 80)

    # Your dataset has nested folders, so don't use */log/*.xml.
    log_files = [
        f
        for f in WITSML_DIR.rglob("*.xml")
        if "/log/" in str(f)
    ]

    print(f"\nLog files found: {len(log_files)}")

    if not log_files:
        print("No log XML files found.")
        return

    all_rows = []

    successful = 0

    for i, xml_file in enumerate(log_files, 1):

        rows = extract_log_file(xml_file)

        if rows:
            successful += 1
            all_rows.extend(rows)

        print(
            f"[{i:>3}/{len(log_files)}] "
            f"{xml_file.name:<12} "
            f"rows={len(rows)}"
        )

    if not all_rows:
        print("\nNo rows extracted.")
        return

    # ---------------------------------------------------------
    # CSV columns
    # ---------------------------------------------------------

    columns = [
        "well_id",
        "source_file",
        "Time",
        "Depth",
        "BITDEP",
        "VBITSDEP",
        "VDEPTH",
        "WOB",
        "RPM",
        "ROP",
        "TORQUE",
        "TQ",
        "TQ_IN_AMPS",
        "TQ_IN_AMPS_AV",
        "FLOWIN",
        "FLOWOUT",
        "FLOWOUTPC",
        "MWIN",
        "MWOUT",
        "MWINANN",
        "MWDLOSS",
        "ECDCS",
        "ECDBIT",
        "PUMP",
        "PUMPPOWER",
        "BITPOWER",
        "JETVEL",
        "BITLOSS",
        "DSTRINGLOSS",
        "MOTORLOSS",
        "SURFLOSS",
        "IMPACT",
        "HCCI",
        "RigActivityCode",
        "EditFlag",
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns,
            extrasaction="ignore"
        )

        writer.writeheader()

        for row in all_rows:
            writer.writerow(row)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)

    print(f"Successful log files : {successful}")
    print(f"Total rows           : {len(all_rows)}")
    print(f"Output               : {OUTPUT_FILE}")

    print("\nChannel availability:")

    for channel in columns[2:]:

        count = sum(
            1
            for row in all_rows
            if row.get(channel) not in (None, "")
        )

        if count > 0:
            print(
                f"{channel:<20} "
                f"{count:>10} values"
            )


if __name__ == "__main__":
    main()
