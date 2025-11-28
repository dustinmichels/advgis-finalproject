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
    "lane_buffered": 8,  # Added buffered lane type
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


def apply_buffer_upgrade(row):
    """Upgrade 'lane' to 'lane_buffered' if cycleway:buffer exists."""

    cycleway_type = row["cycleway_type"]

    if cycleway_type == "lane":
        buffer_val = row.get("cycleway:buffer")
        if buffer_val is None:
            buffer_val = row.get("cycleway:separation")

        # Check if buffer exists and is not empty/no/nan
        if buffer_val is not None and buffer_val != "no":
            if not (isinstance(buffer_val, float) and pd.isna(buffer_val)):
                return "lane_buffered"

    return cycleway_type


def combine_and_score_cycleway_types(df):
    # combine all cycleway vals
    df["cycleway_all"] = df.apply(combine_cycleways, axis=1)

    # pick best
    df["cycleway_type"] = df["cycleway_all"].apply(pick_best)

    # upgrade lane to lane_buffered if buffer exists
    # TODO: maybe do this before picking best?
    df["cycleway_type"] = df.apply(apply_buffer_upgrade, axis=1)

    # check if highway=cycleway OR highway=path + bicycle=designated
    # if so, set cycleway_type to 'separate' and score to 10
    is_cycleway = (df["highway"] == "cycleway") | (
        (df["highway"] == "path") & (df["bicycle"] == "designated")
    )
    df.loc[is_cycleway, "cycleway_type"] = "separate"

    # apply score column
    df["cycleway_score"] = df["cycleway_type"].apply(
        lambda v: CYCLEWAY_RANKING.get(v, 0)
    )

    return df
