"""
What type of cycleway is it?

We combine all cycleway-related tags into a single "cycleway_type" column,
combine all the cycleway tags into a list, pick the "best" cycleway type,
and assign a score based on the type of cycleway.
"""

import numpy as np
import pandas as pd

CYCLEWAY_RANKING = {
    "no": 0,
    "shared_lane": 3,  # in traffic
    "share_busway": 5,  # shared with bus
    "lane": 7,  # dedicated bike lane, not separate
    "lane_buffered": 7.5,  # Added buffered lane type
    "track": 8,  # totally separated (but sometimes used for lane with buffer)
    "separate": 10,  # totally separated
}


def combine_cycleways(row):
    """Accumulate all cycleway values into a single list."""

    cols = ["cycleway", "cycleway:both", "cycleway:left", "cycleway:right"]

    values = []
    for col in cols:
        v = row[col]

        # Normalize: listify arrays
        if isinstance(v, np.ndarray):
            v = v.tolist()

        # Skip missing
        if v is None or v == "no":
            continue
        if isinstance(v, float) and pd.isna(v):
            continue

        # Handle lists
        if isinstance(v, list):
            values.extend(v)
        else:
            values.append(v)

    return values


def pick_best(values):
    return max(values, key=lambda v: CYCLEWAY_RANKING.get(v, 0), default=None)


def apply_buffer_to_list(values, row):
    """Upgrade 'lane' to 'lane_buffered' in a list if buffer exists."""
    buffer_val = row.get("cycleway:buffer")
    if buffer_val is None:
        buffer_val = row.get("cycleway:separation")

    # Check if buffer exists and is valid
    has_buffer = (
        buffer_val is not None
        and buffer_val != "no"
        and not (isinstance(buffer_val, float) and pd.isna(buffer_val))
    )

    if not has_buffer:
        return values

    # Upgrade any 'lane' to 'lane_buffered'
    return ["lane_buffered" if v == "lane" else v for v in values]


def adjust_track_with_separation(row):
    """
    If cycleway is 'track' but separation is 'flex_post' or 'parking_lane', rename to 'lane_buffered'.
    """
    cycleway_all = row["cycleway_all"]
    separation = row.get("cycleway:separation")

    if "track" in cycleway_all and separation in ["flex_post", "parking_lane"]:
        # Replace 'track' with 'lane_buffered'
        cycleway_all = ["lane_buffered" if v == "track" else v for v in cycleway_all]
    return cycleway_all


def combine_and_score_cycleway_types(df):
    # combine all cycleway vals
    df["cycleway_all"] = df.apply(combine_cycleways, axis=1)

    # rename: if buffer exists, rename 'lane' to 'lane_buffered'
    df["cycleway_all"] = df.apply(
        lambda row: apply_buffer_to_list(row["cycleway_all"], row), axis=1
    )

    # rename: if cycleway="track" but cycleway:separation="flex_post," rename to "lane_buffered"
    df["cycleway_all"] = df.apply(adjust_track_with_separation, axis=1)

    # pick best
    df["cycleway_type"] = df["cycleway_all"].apply(pick_best)

    # check if highway=cycleway OR highway=path + bicycle=designated
    # if so, set cycleway_type to 'separate'
    is_cycleway = (df["highway"] == "cycleway") | (
        (df["highway"] == "path") & (df["bicycle"] == "designated")
    )
    df.loc[is_cycleway, "cycleway_type"] = "separate"

    # apply score column
    df["cycleway_score"] = df["cycleway_type"].apply(
        lambda v: CYCLEWAY_RANKING.get(v, 0)
    )

    return df
