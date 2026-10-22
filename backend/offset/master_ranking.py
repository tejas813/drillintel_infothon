from pathlib import Path
import csv
import sys

# Allow imports from backend/
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.offset.trajectory_similarity import (
    load_trajectories,
    calculate_profile_similarity,
    normalize_trajectory,
)

from backend.offset.spatial import spatial_similarity


DATA_DIR = BASE_DIR / "data" / "processed"

INVENTORY_FILE = DATA_DIR / "well_inventory.csv"
LOCATION_FILE = DATA_DIR / "well_locations.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_inventory():
    return load_csv(INVENTORY_FILE)


def load_locations():
    if not LOCATION_FILE.exists():
        return {}

    rows = load_csv(LOCATION_FILE)

    locations = {}

    for row in rows:
        locations[row["well_id"]] = {
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
        }

    return locations


def depth_compatibility(target, offset):
    """
    Compare total measured depth of target and offset wells.

    Returns score between 0 and 1.
    """

    target_md = float(target["max_md"])
    offset_md = float(offset["max_md"])

    difference = abs(target_md - offset_md)

    score = 1.0 / (
        1.0 + difference / max(target_md, 1.0)
    )

    return round(score, 4)


def trajectory_score(target_id, offset_id, trajectories):
    """
    Calculate complete trajectory profile similarity.
    """

    if target_id not in trajectories:
        return 0.0

    if offset_id not in trajectories:
        return 0.0

    target_profile = normalize_trajectory(
        trajectories[target_id]
    )

    offset_profile = normalize_trajectory(
        trajectories[offset_id]
    )

    return calculate_profile_similarity(
        target_profile,
        offset_profile
    )


def calculate_master_score(
    trajectory_score_value,
    depth_score,
    spatial_score=None
):
    """
    Combine available intelligence signals.

    If spatial information is unavailable,
    weights are automatically redistributed.
    """

    if spatial_score is None:

        # No valid coordinates available.
        final_score = (
            0.70 * trajectory_score_value
            + 0.30 * depth_score
        )

    else:

        final_score = (
            0.50 * trajectory_score_value
            + 0.20 * depth_score
            + 0.30 * spatial_score
        )

    return round(final_score, 4)


def rank_offset_wells(target_well_id, top_k=5):

    inventory = load_inventory()
    trajectories = load_trajectories()
    locations = load_locations()

    target = None

    for well in inventory:
        if well["well_id"] == target_well_id:
            target = well
            break

    if target is None:
        raise ValueError(
            f"Target well not found: {target_well_id}"
        )

    results = []

    for candidate in inventory:

        offset_id = candidate["well_id"]

        if offset_id == target_well_id:
            continue

        # ----------------------------------------
        # 1. Trajectory similarity
        # ----------------------------------------

        traj_score = trajectory_score(
            target_well_id,
            offset_id,
            trajectories
        )

        # ----------------------------------------
        # 2. Depth compatibility
        # ----------------------------------------

        depth_score = depth_compatibility(
            target,
            candidate
        )

        # ----------------------------------------
        # 3. Spatial similarity
        # ----------------------------------------

        target_location = locations.get(
            target_well_id,
            {}
        )

        offset_location = locations.get(
            offset_id,
            {}
        )

        spatial = spatial_similarity(
            target_location.get("latitude"),
            target_location.get("longitude"),
            offset_location.get("latitude"),
            offset_location.get("longitude"),
        )

        spatial_score = spatial["score"]

        # ----------------------------------------
        # 4. Master score
        # ----------------------------------------

        final_score = calculate_master_score(
            traj_score,
            depth_score,
            spatial_score
        )

        results.append({
            "target_well": target_well_id,
            "offset_well": offset_id,

            "trajectory_score": traj_score,

            "depth_score": depth_score,

            "spatial_score": spatial_score,

            "distance_km": spatial["distance_km"],

            "final_score": final_score,
        })

    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results[:top_k]


def main():

    print()
    print("=" * 78)
    print("eRTMAC-NWIS | MASTER OFFSET WELL RANKING")
    print("=" * 78)
    print()

    inventory = load_inventory()

    if len(inventory) < 2:
        print("ERROR: At least two wells are required.")
        return

    target_well = inventory[0]["well_id"]

    print(f"Target Well: {target_well}")
    print()

    results = rank_offset_wells(
        target_well,
        top_k=5
    )

    print(
        f"{'Rank':<6}"
        f"{'Offset Well':<38}"
        f"{'Trajectory':<12}"
        f"{'Depth':<10}"
        f"{'Spatial':<10}"
        f"{'FINAL':<10}"
    )

    print("-" * 86)

    for rank, result in enumerate(
        results,
        start=1
    ):

        spatial_display = (
            f"{result['spatial_score']:.4f}"
            if result["spatial_score"] is not None
            else "N/A"
        )

        print(
            f"{rank:<6}"
            f"{result['offset_well']:<38}"
            f"{result['trajectory_score']:<12.4f}"
            f"{result['depth_score']:<10.4f}"
            f"{spatial_display:<10}"
            f"{result['final_score']:<10.4f}"
        )

    print()
    print("=" * 78)
    print("MASTER RANKING COMPLETED")
    print("=" * 78)
    print()


if __name__ == "__main__":
    main()
