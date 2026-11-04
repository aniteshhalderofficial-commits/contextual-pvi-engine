import json
from pathlib import Path

import pandas as pd

from parser import (
    load_match,
    parse_match_metadata,
    parse_innings,
    parse_deliveries,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATCHES_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "cricsheet"
    / "matches"
)

METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "match_metadata.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


def get_t20_match_ids():
    """Get men's T20/IT20 match IDs from the existing metadata index."""

    metadata = pd.read_csv(
        METADATA_FILE,
        low_memory=False
    )

    filtered = metadata[
        (metadata["gender"] == "male")
        & (metadata["match_type"].isin(["T20", "IT20"]))
    ]

    return (
        filtered["match_id"]
        .astype(str)
        .tolist()
    )


def build_datasets():
    """Build canonical match, innings, and delivery datasets."""

    match_records = []
    innings_records = []
    delivery_records = []

    match_ids = get_t20_match_ids()

    total_matches = len(match_ids)

    print(
        f"Building canonical datasets for "
        f"{total_matches} men's T20/IT20 matches..."
    )

    for index, match_id in enumerate(match_ids, start=1):

        match_file = MATCHES_DIR / f"{match_id}.json"

        if not match_file.exists():
            print(
                f"WARNING: Missing match file: {match_id}.json"
            )
            continue

        try:
            data = load_match(match_file)

            # Match metadata
            metadata = parse_match_metadata(
                data,
                match_id
            )

            match_records.append(metadata)

            # Innings
            innings = parse_innings(
                data,
                match_id
            )

            innings_records.extend(innings)

            # Deliveries
            deliveries = parse_deliveries(
                data,
                match_id
            )

            delivery_records.extend(deliveries)

        except Exception as exc:
            print(
                f"ERROR processing {match_id}: "
                f"{type(exc).__name__}: {exc}"
            )

        if index % 100 == 0 or index == total_matches:
            print(
                f"Processed {index}/{total_matches} matches"
            )

    print("\nCreating DataFrames...")

    match_df = pd.DataFrame(match_records)

    innings_df = pd.DataFrame(innings_records)

    delivery_df = pd.DataFrame(delivery_records)

    # Serialize nested delivery fields as JSON strings.
    if not delivery_df.empty:
        delivery_df["wicket_events"] = (
            delivery_df["wicket_events"]
            .apply(json.dumps)
        )

        delivery_df["fielders_involved"] = (
            delivery_df["fielders_involved"]
            .apply(json.dumps)
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    match_output = (
        OUTPUT_DIR
        / "match_metadata.csv"
    )

    innings_output = (
        OUTPUT_DIR
        / "innings.csv"
    )

    delivery_output = (
        OUTPUT_DIR
        / "deliveries.csv"
    )

    print("\nWriting datasets...")

    match_df.to_csv(
        match_output,
        index=False
    )

    innings_df.to_csv(
        innings_output,
        index=False
    )

    delivery_df.to_csv(
        delivery_output,
        index=False
    )

    print("\n" + "=" * 60)
    print("CANONICAL DATASET BUILD COMPLETE")
    print("=" * 60)

    print(
        f"Matches:    {len(match_df):,}"
    )

    print(
        f"Innings:    {len(innings_df):,}"
    )

    print(
        f"Deliveries: {len(delivery_df):,}"
    )

    print("\nFiles created:")

    print(
        f"  {match_output}"
    )

    print(
        f"  {innings_output}"
    )

    print(
        f"  {delivery_output}"
    )


if __name__ == "__main__":
    build_datasets()