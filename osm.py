import re

import numpy as np
import osmnx as ox
import pandas as pd

FEET_TO_M = 0.3048


def extract_maxspeed(x) -> float:
    # Handle NaN early
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan

    # Handle lists and numpy arrays uniformly
    if isinstance(x, (list, np.ndarray)):
        speeds = [extract_maxspeed(i) for i in x]
        # filter out NaNs
        speeds = [s for s in speeds if not pd.isna(s)]
        return max(speeds) if speeds else np.nan

    # Convert to string and extract digits
    x_str = str(x)
    nums = re.findall(r"\d+", x_str)

    return int(max(nums, key=int)) if nums else np.nan


def extract_width(value):
    # If list, use first value
    if isinstance(value, list):
        value = value[0]

    """Return numeric width in meters from OSM width tags."""
    if pd.isna(value):
        return None

    s = str(value).strip()

    # Feet notation like 9'
    if "'" in s:
        match = re.search(r"\d+(\.\d+)?", s)
        if match:
            return float(match.group()) * FEET_TO_M
        else:
            return None

    # Standard numeric meters
    match = re.search(r"\d+(\.\d+)?", s)
    if match:
        return float(match.group())

    return None


def get_network(place: str, network_type: str):
    G = ox.graph_from_place(place, network_type=network_type)
    _, edges = ox.graph_to_gdfs(G)

    # parse maxspeed and width
    edges["maxspeed_int"] = edges["maxspeed"].apply(extract_maxspeed)
    edges["width_float"] = edges["width"].apply(extract_width)

    # drop some unneeded columns
    edges = edges.drop(
        ["ref", "service", "access", "bridge", "tunnel", "junction"], axis=1
    )

    # add buffer column (half of width)
    edges["buffer_dist"] = edges["width_float"] / 2.0

    return edges


def main():
    place = "Somerville, Massachusetts, USA"

    print("Get bike network")
    edges_bike = get_network(place, "bike")

    print("Saving to GeoPackage")
    edges_bike.to_file(
        "data/somerville_bike_network.gpkg", layer="edges", driver="GPKG"
    )


if __name__ == "__main__":
    main()
