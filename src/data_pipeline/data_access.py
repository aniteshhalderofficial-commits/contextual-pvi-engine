from pathlib import Path

import pandas as pd


# Project root:
# contextual-pvi-engine/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MATCH_METADATA_FILE = PROCESSED_DIR / "match_metadata.csv"
INNINGS_FILE = PROCESSED_DIR / "innings.csv"
DELIVERIES_FILE = PROCESSED_DIR / "deliveries.csv"


def load_match_metadata(match_id=None):
    """
    Load match metadata.

    Parameters
    ----------
    match_id : str, optional
        If provided, return metadata for only this match.

    Returns
    -------
    pandas.DataFrame
        Match metadata records.
    """
    df = pd.read_csv(MATCH_METADATA_FILE)

    if match_id is not None:
        match_id = str(match_id)
        df = df[df["match_id"].astype(str) == match_id]

    return df.reset_index(drop=True)


def load_innings(match_id):
    """
    Load innings data for a specific match.

    Parameters
    ----------
    match_id : str
        Cricsheet match ID.

    Returns
    -------
    pandas.DataFrame
        Innings records for the requested match.
    """
    match_id = str(match_id)

    df = pd.read_csv(INNINGS_FILE)
    df = df[df["match_id"].astype(str) == match_id]

    return df.reset_index(drop=True)


def load_deliveries(match_id, innings_number=None):
    """
    Load delivery data for a specific match.

    Parameters
    ----------
    match_id : str
        Cricsheet match ID.

    innings_number : int, optional
        If provided, return deliveries only for this innings.

    Returns
    -------
    pandas.DataFrame
        Delivery records for the requested match/innings.
    """
    match_id = str(match_id)

    df = pd.read_csv(DELIVERIES_FILE)

    df = df[df["match_id"].astype(str) == match_id]

    if innings_number is not None:
        df = df[df["innings_number"] == innings_number]

    return df.reset_index(drop=True)


def load_match(match_id):
    """
    Load all processed data for a specific match.

    Parameters
    ----------
    match_id : str
        Cricsheet match ID.

    Returns
    -------
    dict
        Dictionary containing match metadata, innings, and deliveries.
    """
    return {
        "match_metadata": load_match_metadata(match_id),
        "innings": load_innings(match_id),
        "deliveries": load_deliveries(match_id),
    }