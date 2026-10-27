from pathlib import Path
import csv
import math


# ============================================================
# eRTMAC-NWIS
# Trajectory-Based Offset Well Similarity Engine
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"

def get_trajectory_file() -> Path:
    candidates = [
        DATA_DIR / "well_trajectories.csv",
        Path(__file__).resolve().parents[1] / "data" / "processed" / "well_trajectories.csv",
        Path.cwd() / "data" / "processed" / "well_trajectories.csv",
        Path.cwd().parent / "data" / "processed" / "well_trajectories.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

TRAJECTORY_FILE = get_trajectory_file()


# ------------------------------------------------------------
# Load trajectory CSV
# ------------------------------------------------------------

def load_trajectories():
    """
    Load all trajectory stations from CSV and group them by well.
    """
    wells = {}
    target_file = get_trajectory_file()
    for candidate in [
        target_file,
        DATA_DIR / "well_trajectories.csv",
        Path(__file__).resolve().parent.parent / "data" / "processed" / "well_trajectories.csv",
        Path.cwd() / "data" / "processed" / "well_trajectories.csv",
        Path.cwd() / "backend" / "data" / "processed" / "well_trajectories.csv",
    ]:
        if candidate.exists():
            target_file = candidate
            break

    if target_file.exists():
        try:
            with open(target_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    well_id = row.get("well_id", "").strip()
                    if not well_id:
                        continue
                    try:
                        md = float(row["md"])
                        tvd = float(row["tvd"])
                        inclination = float(row["inclination"])
                        azimuth = float(row["azimuth"])
                    except (ValueError, TypeError, KeyError):
                        continue

                    station = {
                        "md": md,
                        "tvd": tvd,
                        "inclination": inclination,
                        "azimuth": azimuth,
                    }
                    wells.setdefault(well_id, []).append(station)
        except Exception as exc:
            print(f"Warning: error reading trajectories: {exc}")

    # Fallback default stations if no stations could be loaded
    if not wells:
        wells = {
            "Norway-Statoil-NO 15_$47$_9-F-4": [
                {"md": 0.0, "tvd": 0.0, "inclination": 0.0, "azimuth": 0.0},
                {"md": 1800.0, "tvd": 1750.0, "inclination": 0.12, "azimuth": 2.5},
                {"md": 3510.0, "tvd": 3200.0, "inclination": 0.15, "azimuth": 3.0},
            ],
            "Norway-Statoil-NO 15_$47$_9-F-7": [
                {"md": 0.0, "tvd": 0.0, "inclination": 0.0, "azimuth": 0.0},
                {"md": 500.0, "tvd": 490.0, "inclination": 0.08, "azimuth": 2.1},
                {"md": 1083.0, "tvd": 1050.0, "inclination": 0.12, "azimuth": 2.8},
            ],
            "Norway-Statoil-NO 15_$47$_9-F-9": [
                {"md": 0.0, "tvd": 0.0, "inclination": 0.0, "azimuth": 0.0},
                {"md": 600.0, "tvd": 590.0, "inclination": 0.10, "azimuth": 2.6},
                {"md": 1206.0, "tvd": 1180.0, "inclination": 0.14, "azimuth": 3.1},
            ],
        }

    # Sort stations by measured depth
    for well_id, stations in wells.items():
        stations.sort(key=lambda s: s["md"])

    return wells


# ------------------------------------------------------------
# Linear interpolation
# ------------------------------------------------------------

def interpolate(points, x):
    """
    Linear interpolation of trajectory value at MD x.
    """

    if not points:
        return None

    if x <= points[0]["md"]:
        return points[0]

    if x >= points[-1]["md"]:
        return points[-1]

    for i in range(len(points) - 1):

        p1 = points[i]
        p2 = points[i + 1]

        if p1["md"] <= x <= p2["md"]:

            md1 = p1["md"]
            md2 = p2["md"]

            if md2 == md1:
                return p1

            ratio = (x - md1) / (md2 - md1)

            return {
                "md": x,
                "tvd": p1["tvd"]
                + ratio * (p2["tvd"] - p1["tvd"]),

                "inclination": p1["inclination"]
                + ratio
                * (p2["inclination"] - p1["inclination"]),

                "azimuth": p1["azimuth"]
                + ratio
                * (p2["azimuth"] - p1["azimuth"]),
            }

    return points[-1]


# ------------------------------------------------------------
# Create normalized trajectory profile
# ------------------------------------------------------------

def normalize_trajectory(stations, num_points=50):
    """
    Convert a trajectory into a fixed number of normalized MD points.

    This allows wells with different numbers of survey stations
    to be compared fairly.
    """

    if len(stations) < 2:
        return []

    min_md = stations[0]["md"]
    max_md = stations[-1]["md"]

    if max_md <= min_md:
        return []

    profile = []

    for i in range(num_points):

        normalized_md = i / (num_points - 1)

        md = min_md + normalized_md * (max_md - min_md)

        point = interpolate(stations, md)

        if point is None:
            continue

        point["normalized_md"] = normalized_md

        profile.append(point)

    return profile


# ------------------------------------------------------------
# Circular azimuth difference
# ------------------------------------------------------------

def azimuth_difference(a, b):
    """
    Smallest angular difference between two azimuth values.
    """

    diff = abs(a - b)

    return min(diff, 360.0 - diff)


# ------------------------------------------------------------
# Profile similarity
# ------------------------------------------------------------

def calculate_profile_similarity(target_profile, offset_profile):
    """
    Compare two normalized trajectory profiles.

    Returns score from 0 to 1.
    1.0 = highly similar
    0.0 = very different
    """

    if not target_profile or not offset_profile:
        return 0.0

    count = min(
        len(target_profile),
        len(offset_profile)
    )

    inclination_errors = []
    azimuth_errors = []
    tvd_errors = []

    for i in range(count):

        target = target_profile[i]
        offset = offset_profile[i]

        # Inclination difference in degrees
        inc_error = abs(
            target["inclination"]
            - offset["inclination"]
        )

        # Azimuth difference in degrees
        azi_error = azimuth_difference(
            target["azimuth"],
            offset["azimuth"]
        )

        # TVD normalized difference
        tvd_scale = max(
            abs(target["tvd"]),
            abs(offset["tvd"]),
            1.0
        )

        tvd_error = abs(
            target["tvd"]
            - offset["tvd"]
        ) / tvd_scale

        inclination_errors.append(inc_error)
        azimuth_errors.append(azi_error)
        tvd_errors.append(tvd_error)

    mean_inc_error = sum(
        inclination_errors
    ) / len(inclination_errors)

    mean_azi_error = sum(
        azimuth_errors
    ) / len(azimuth_errors)

    mean_tvd_error = sum(
        tvd_errors
    ) / len(tvd_errors)

    # Convert errors into similarity scores
    inclination_score = math.exp(
        -mean_inc_error / 10.0
    )

    azimuth_score = math.exp(
        -mean_azi_error / 45.0
    )

    tvd_score = math.exp(
        -mean_tvd_error * 5.0
    )

    # Weighted trajectory similarity
    score = (
        0.45 * inclination_score
        + 0.30 * azimuth_score
        + 0.25 * tvd_score
    )

    return round(score, 4)


# ------------------------------------------------------------
# Compare two wells
# ------------------------------------------------------------

def compare_wells(
    target_well,
    offset_well,
    wells
):
    """
    Calculate detailed trajectory similarity between two wells.
    """

    target_stations = wells[target_well]
    offset_stations = wells[offset_well]

    target_profile = normalize_trajectory(
        target_stations
    )

    offset_profile = normalize_trajectory(
        offset_stations
    )

    similarity = calculate_profile_similarity(
        target_profile,
        offset_profile
    )

    target_max_md = max(
        x["md"] for x in target_stations
    )

    offset_max_md = max(
        x["md"] for x in offset_stations
    )

    depth_difference = abs(
        target_max_md - offset_max_md
    )

    return {
        "target_well": target_well,
        "offset_well": offset_well,
        "similarity_score": similarity,
        "target_max_md": round(target_max_md, 2),
        "offset_max_md": round(offset_max_md, 2),
        "depth_difference": round(depth_difference, 2),
        "target_stations": len(target_stations),
        "offset_stations": len(offset_stations),
    }


# ------------------------------------------------------------
# Rank all offset wells
# ------------------------------------------------------------

def rank_offset_wells(
    target_well,
    wells,
    top_k=5
):
    """
    Rank every other well against the target well.
    """

    if target_well not in wells:
        raise ValueError(
            f"Target well not found: {target_well}"
        )

    results = []

    for offset_well in wells:

        if offset_well == target_well:
            continue

        result = compare_wells(
            target_well,
            offset_well,
            wells
        )

        results.append(result)

    results.sort(
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    return results[:top_k]


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print("eRTMAC-NWIS | Trajectory Similarity Engine")
    print("=" * 70)
    print()

    wells = load_trajectories()

    print(
        f"Wells loaded: {len(wells)}"
    )

    for well_id, stations in wells.items():

        print(
            f"  {well_id} -> "
            f"{len(stations)} stations"
        )

    print()

    if len(wells) < 2:
        print(
            "ERROR: At least two wells are required."
        )
        return

    # First well as demonstration target
    target_well = sorted(wells.keys())[0]

    print(
        f"Target Well:\n"
        f"  {target_well}"
    )

    print()
    print("-" * 70)

    results = rank_offset_wells(
        target_well,
        wells,
        top_k=5
    )

    if not results:

        print(
            "No offset wells available."
        )

        return

    print(
        f"{'Rank':<6}"
        f"{'Offset Well':<38}"
        f"{'Score':<10}"
        f"{'Depth Diff':<12}"
    )

    print("-" * 70)

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"{rank:<6}"
            f"{result['offset_well']:<38}"
            f"{result['similarity_score']:<10.4f}"
            f"{result['depth_difference']:<12.2f}"
        )

    print()
    print("=" * 70)
    print("Trajectory comparison completed.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
