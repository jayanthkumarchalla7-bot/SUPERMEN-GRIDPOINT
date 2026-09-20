import numpy as np


def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate geographic distance between two
    latitude/longitude points.

    Returns distance in kilometers.
    """

    earth_radius = 6371.0

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arctan2(
        np.sqrt(a),
        np.sqrt(1 - a)
    )

    return earth_radius * c


def create_distance_matrix(
    neighborhoods,
    candidate_locations
):
    """
    Creates distance matrix.

    Rows    = neighborhoods
    Columns = candidate warehouse locations
    """

    n = len(neighborhoods)
    m = len(candidate_locations)

    matrix = np.zeros((n, m))

    for i in range(n):

        for j in range(m):

            matrix[i][j] = haversine_distance(
                neighborhoods.iloc[i]["latitude"],
                neighborhoods.iloc[i]["longitude"],
                candidate_locations.iloc[j]["latitude"],
                candidate_locations.iloc[j]["longitude"]
            )

    return matrix