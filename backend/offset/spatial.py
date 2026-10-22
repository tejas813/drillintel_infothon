from math import radians, sin, cos, sqrt, atan2


def haversine_distance_km(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):
    """
    Calculate great-circle distance between two coordinates.
    Returns distance in kilometres.
    """

    lat1 = radians(latitude1)
    lon1 = radians(longitude1)
    lat2 = radians(latitude2)
    lon2 = radians(longitude2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    earth_radius_km = 6371.0

    return earth_radius_km * c


def coordinates_available(
    latitude,
    longitude
):
    """
    Check whether valid well coordinates are available.

    0,0 is treated as missing because the current
    Volve WITSML files do not provide real coordinates.
    """

    if latitude is None or longitude is None:
        return False

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return False

    if latitude == 0 and longitude == 0:
        return False

    if not (-90 <= latitude <= 90):
        return False

    if not (-180 <= longitude <= 180):
        return False

    return True


def spatial_similarity(
    target_latitude,
    target_longitude,
    offset_latitude,
    offset_longitude
):
    """
    Convert geographical distance into a similarity score.

    Returns:
        {
            "available": bool,
            "distance_km": float | None,
            "score": float | None
        }
    """

    if not coordinates_available(
        target_latitude,
        target_longitude
    ):
        return {
            "available": False,
            "distance_km": None,
            "score": None
        }

    if not coordinates_available(
        offset_latitude,
        offset_longitude
    ):
        return {
            "available": False,
            "distance_km": None,
            "score": None
        }

    distance = haversine_distance_km(
        float(target_latitude),
        float(target_longitude),
        float(offset_latitude),
        float(offset_longitude)
    )

    # Nearby wells get a higher score.
    score = 1.0 / (1.0 + distance)

    return {
        "available": True,
        "distance_km": round(distance, 4),
        "score": round(score, 4)
    }


if __name__ == "__main__":

    print("eRTMAC-NWIS | Spatial Intelligence")
    print("-" * 50)

    result = spatial_similarity(
        0,
        0,
        0,
        0
    )

    print("Test coordinates: 0,0 → 0,0")
    print(f"Available: {result['available']}")
    print(f"Distance:  {result['distance_km']}")
    print(f"Score:     {result['score']}")

    print("-" * 50)
