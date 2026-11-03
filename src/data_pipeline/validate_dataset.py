import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd


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


def load_match(file_path):
    """Load one Cricsheet JSON match."""
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_t20_match_ids():
    """
    Get men's T20/IT20 match IDs from the existing
    match metadata index.

    This avoids opening all 18,489 JSON files just
    to discover which ones are T20/IT20.
    """

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_FILE}"
        )

    df = pd.read_csv(METADATA_FILE)

    filtered = df[
        (df["gender"] == "male")
        & (
            df["match_type"].isin(
                ["T20", "IT20"]
            )
        )
    ]

    return filtered["match_id"].astype(str).tolist()


def validate_match(file_path):
    """
    Validate one men's T20/IT20 match.

    Checks:
    - basic match structure
    - innings structure
    - delivery ordering
    - duplicate canonical delivery keys
    - run consistency
    - extras consistency
    - legal delivery counting
    - wicket-event consistency
    - innings totals
    """

    data = load_match(file_path)
    info = data.get("info", {})

    errors = []
    warnings = []

    match_id = file_path.stem
    teams = info.get("teams", [])

    if len(teams) != 2:
        errors.append(
            "Match does not contain exactly two teams"
        )

    if info.get("gender") != "male":
        errors.append(
            "Match is not men's cricket"
        )

    if info.get("match_type") not in {
        "T20",
        "IT20",
    }:
        errors.append(
            "Match is not T20/IT20"
        )

    innings_list = data.get("innings", [])

    if not innings_list:
        errors.append(
            "No innings found"
        )

    total_deliveries = 0
    total_legal_deliveries = 0
    total_wicket_events = 0
    total_wickets_lost = 0

    duplicate_delivery_keys = []

    canonical_delivery_keys = set()

    wicket_kind_counter = Counter()

    innings_results = []

    for innings_number, innings in enumerate(
        innings_list,
        start=1
    ):
        batting_team = innings.get("team")

        if batting_team not in teams:
            errors.append(
                f"Innings {innings_number}: "
                f"batting team '{batting_team}' "
                f"not in match teams"
            )

        innings_runs = 0
        innings_extras = 0

        innings_wicket_events = 0
        innings_wickets_lost = 0
        innings_legal_deliveries = 0

        previous_over = -1

        for over in innings.get("overs", []):
            over_number = over.get("over")

            if over_number is None:
                errors.append(
                    f"Innings {innings_number}: "
                    f"missing over number"
                )
                continue

            if over_number < previous_over:
                errors.append(
                    f"Innings {innings_number}: "
                    f"overs are not ordered"
                )

            if over_number == previous_over:
                errors.append(
                    f"Innings {innings_number}: "
                    f"duplicate over number "
                    f"{over_number}"
                )

            previous_over = over_number

            deliveries = over.get(
                "deliveries",
                []
            )

            for sequence, delivery in enumerate(
                deliveries,
                start=1
            ):
                total_deliveries += 1

                # -------------------------------------------------
                # Canonical delivery key
                # -------------------------------------------------

                canonical_key = (
                    match_id,
                    innings_number,
                    over_number,
                    sequence,
                )

                if canonical_key in canonical_delivery_keys:
                    duplicate_delivery_keys.append(
                        canonical_key
                    )

                canonical_delivery_keys.add(
                    canonical_key
                )

                # -------------------------------------------------
                # Player fields
                # -------------------------------------------------

                if not delivery.get("batter"):
                    errors.append(
                        f"Innings {innings_number}, "
                        f"over {over_number}, "
                        f"delivery {sequence}: "
                        f"missing batter"
                    )

                if not delivery.get("bowler"):
                    errors.append(
                        f"Innings {innings_number}, "
                        f"over {over_number}, "
                        f"delivery {sequence}: "
                        f"missing bowler"
                    )

                if not delivery.get("non_striker"):
                    errors.append(
                        f"Innings {innings_number}, "
                        f"over {over_number}, "
                        f"delivery {sequence}: "
                        f"missing non-striker"
                    )

                # -------------------------------------------------
                # Runs
                # -------------------------------------------------

                runs = delivery.get("runs") or {}

                batter_runs = runs.get(
                    "batter",
                    0
                )

                extra_runs = runs.get(
                    "extras",
                    0
                )

                total_runs = runs.get(
                    "total",
                    0
                )

                if batter_runs < 0:
                    errors.append(
                        f"Innings {innings_number}: "
                        f"negative batter runs"
                    )

                if extra_runs < 0:
                    errors.append(
                        f"Innings {innings_number}: "
                        f"negative extra runs"
                    )

                if total_runs < 0:
                    errors.append(
                        f"Innings {innings_number}: "
                        f"negative total runs"
                    )

                if (
                    batter_runs
                    + extra_runs
                    != total_runs
                ):
                    errors.append(
                        f"Innings {innings_number}, "
                        f"over {over_number}, "
                        f"delivery {sequence}: "
                        f"run components do not add up"
                    )

                innings_runs += total_runs
                innings_extras += extra_runs

                # -------------------------------------------------
                # Extras
                # -------------------------------------------------

                extras = delivery.get(
                    "extras"
                ) or {}

                categorized_extras = sum(
                    value
                    for value in extras.values()
                    if isinstance(
                        value,
                        (int, float)
                    )
                )

                if categorized_extras != extra_runs:
                    errors.append(
                        f"Innings {innings_number}, "
                        f"over {over_number}, "
                        f"delivery {sequence}: "
                        f"extras categories "
                        f"({categorized_extras}) "
                        f"do not equal runs.extras "
                        f"({extra_runs})"
                    )

                known_extra_keys = {
                    "wides",
                    "noballs",
                    "byes",
                    "legbyes",
                    "penalty",
                }

                unknown_extra_keys = [
                    key
                    for key in extras
                    if key not in known_extra_keys
                ]

                if unknown_extra_keys:
                    warnings.append(
                        f"Innings {innings_number}, "
                        f"over {over_number}, "
                        f"delivery {sequence}: "
                        f"unknown extra types "
                        f"{unknown_extra_keys}"
                    )

                # -------------------------------------------------
                # Legal delivery
                # -------------------------------------------------

                wide_runs = extras.get(
                    "wides",
                    0
                )

                no_ball_runs = extras.get(
                    "noballs",
                    0
                )

                is_legal_delivery = (
                    wide_runs == 0
                    and no_ball_runs == 0
                )

                if is_legal_delivery:
                    total_legal_deliveries += 1
                    innings_legal_deliveries += 1

                # -------------------------------------------------
                # Wickets
                # -------------------------------------------------

                wickets = delivery.get(
                    "wickets"
                ) or []

                total_wicket_events += len(
                    wickets
                )

                innings_wicket_events += len(
                    wickets
                )

                for wicket in wickets:
                    wicket_kind = wicket.get(
                        "kind"
                    )

                    wicket_kind_counter[
                        wicket_kind
                    ] += 1

                    # Retired hurt is recorded as an event,
                    # but is not a wicket lost.
                    if wicket_kind != "retired hurt":
                        total_wickets_lost += 1
                        innings_wickets_lost += 1

                if (
                    innings_wicket_events
                    < innings_wickets_lost
                ):
                    errors.append(
                        f"Innings {innings_number}: "
                        f"wickets lost exceed "
                        f"wicket events"
                    )

        innings_results.append({
            "innings_number": innings_number,
            "total_runs": innings_runs,
            "total_extras": innings_extras,
            "wicket_events": innings_wicket_events,
            "wickets_lost": innings_wickets_lost,
            "legal_deliveries": innings_legal_deliveries,
        })

    if duplicate_delivery_keys:
        errors.append(
            f"Duplicate canonical delivery keys: "
            f"{len(duplicate_delivery_keys)}"
        )

    if total_wickets_lost > total_wicket_events:
        errors.append(
            "Total wickets lost exceed "
            "total recorded wicket events"
        )

    return {
        "match_id": match_id,
        "errors": errors,
        "warnings": warnings,
        "total_deliveries": total_deliveries,
        "total_legal_deliveries": (
            total_legal_deliveries
        ),
        "total_wicket_events": (
            total_wicket_events
        ),
        "total_wickets_lost": (
            total_wickets_lost
        ),
        "duplicate_delivery_keys": len(
            duplicate_delivery_keys
        ),
        "wicket_kinds": dict(
            wicket_kind_counter
        ),
        "innings_results": innings_results,
    }


def run_validation(match_ids):
    """Validate the requested match IDs."""

    valid_matches = 0
    invalid_matches = 0

    total_errors = 0
    total_warnings = 0

    total_deliveries = 0
    total_legal_deliveries = 0

    total_wicket_events = 0
    total_wickets_lost = 0

    duplicate_delivery_keys = 0

    error_counts = Counter()
    wicket_kind_counts = Counter()

    for index, match_id in enumerate(
        match_ids,
        start=1
    ):
        file_path = (
            MATCHES_DIR
            / f"{match_id}.json"
        )

        if not file_path.exists():
            print(
                f"\n❌ {match_id}: "
                f"JSON file not found"
            )
            invalid_matches += 1
            total_errors += 1
            continue

        try:
            result = validate_match(
                file_path
            )

        except Exception as exc:
            print(
                f"\n❌ {match_id}: "
                f"validation crashed: {exc}"
            )
            invalid_matches += 1
            total_errors += 1
            continue

        total_deliveries += result[
            "total_deliveries"
        ]

        total_legal_deliveries += result[
            "total_legal_deliveries"
        ]

        total_wicket_events += result[
            "total_wicket_events"
        ]

        total_wickets_lost += result[
            "total_wickets_lost"
        ]

        duplicate_delivery_keys += result[
            "duplicate_delivery_keys"
        ]

        total_errors += len(
            result["errors"]
        )

        total_warnings += len(
            result["warnings"]
        )

        if result["errors"]:
            invalid_matches += 1

            for error in result["errors"]:
                error_counts[
                    error.split(":")[0]
                ] += 1

            print(
                f"\n❌ {result['match_id']}"
            )

            for error in result["errors"][:10]:
                print(
                    f"   - {error}"
                )

        else:
            valid_matches += 1

        for kind, count in result[
            "wicket_kinds"
        ].items():
            wicket_kind_counts[
                kind
            ] += count

        # More frequent progress for long full runs.
        if (
            index % 100 == 0
            or index == len(match_ids)
        ):
            print(
                f"Processed "
                f"{index}/{len(match_ids)}"
            )

    return {
        "matches_tested": len(match_ids),
        "valid_matches": valid_matches,
        "invalid_matches": invalid_matches,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "total_deliveries": total_deliveries,
        "total_legal_deliveries": (
            total_legal_deliveries
        ),
        "total_wicket_events": (
            total_wicket_events
        ),
        "total_wickets_lost": (
            total_wickets_lost
        ),
        "duplicate_delivery_keys": (
            duplicate_delivery_keys
        ),
        "error_counts": dict(
            error_counts
        ),
        "wicket_kind_counts": dict(
            wicket_kind_counts
        ),
    }


def print_summary(title, result):
    """Print a validation summary."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(
        f"Matches tested:          "
        f"{result['matches_tested']}"
    )

    print(
        f"Valid matches:           "
        f"{result['valid_matches']}"
    )

    print(
        f"Invalid matches:         "
        f"{result['invalid_matches']}"
    )

    print(
        f"Total errors:            "
        f"{result['total_errors']}"
    )

    print(
        f"Total warnings:          "
        f"{result['total_warnings']}"
    )

    print(
        f"Total deliveries:        "
        f"{result['total_deliveries']}"
    )

    print(
        f"Legal deliveries:        "
        f"{result['total_legal_deliveries']}"
    )

    print(
        f"Wicket events:           "
        f"{result['total_wicket_events']}"
    )

    print(
        f"Wickets lost:            "
        f"{result['total_wickets_lost']}"
    )

    print(
        f"Duplicate delivery keys:"
        f" {result['duplicate_delivery_keys']}"
    )

    if result["wicket_kind_counts"]:
        print("\nWicket kinds:")

        for kind, count in sorted(
            result["wicket_kind_counts"].items()
        ):
            print(
                f"  {kind}: {count}"
            )


def main():
    """
    Usage:

        python validate_dataset.py quick
        python validate_dataset.py full
    """

    match_ids = get_t20_match_ids()

    print(
        f"Men's T20/IT20 matches indexed: "
        f"{len(match_ids)}"
    )

    mode = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else "quick"
    )

    if mode == "quick":
        selected_ids = match_ids[:100]

        print(
            "\nRunning QUICK validation "
            "on first 100 matches..."
        )

        result = run_validation(
            selected_ids
        )

        print_summary(
            "QUICK VALIDATION SUMMARY",
            result
        )

    elif mode == "full":
        selected_ids = match_ids

        print(
            "\nRunning FULL validation "
            f"on all {len(selected_ids)} matches..."
        )

        result = run_validation(
            selected_ids
        )

        print_summary(
            "FULL DATASET VALIDATION SUMMARY",
            result
        )

    else:
        print(
            "Invalid mode."
        )

        print(
            "Use either:"
        )

        print(
            "  python validate_dataset.py quick"
        )

        print(
            "  python validate_dataset.py full"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()