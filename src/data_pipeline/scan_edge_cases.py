import csv
import json
from pathlib import Path


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


def get_t20_match_ids():
    """Read men's T20/IT20 match IDs from the metadata CSV."""

    match_ids = []

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            if (
                row["gender"] == "male"
                and row["match_type"] in {"T20", "IT20"}
            ):
                match_ids.append(row["match_id"])

    return match_ids


def main():

    match_ids = get_t20_match_ids()

    print(
        f"Men's T20/IT20 matches to scan: {len(match_ids)}"
    )

    counts = {
        "matches": 0,
        "super_over_matches": 0,
        "dls_matches": 0,
        "penalty_matches": 0,
        "non_boundary_matches": 0,
        "multi_wicket_matches": 0,
        "no_ball_matches": 0,
        "wide_matches": 0,
    }

    examples = {
        "super_over": None,
        "dls": None,
        "penalty": None,
        "non_boundary": None,
        "multi_wicket": None,
        "no_ball": None,
        "wide": None,
    }

    for index, match_id in enumerate(match_ids, start=1):

        file_path = MATCHES_DIR / f"{match_id}.json"

        if not file_path.exists():
            continue

        with file_path.open(
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        counts["matches"] += 1

        info = data.get("info", {})
        outcome = info.get("outcome") or {}

        # -------------------------
        # DLS / revised target
        # -------------------------

        if outcome.get("method") == "D/L":

            counts["dls_matches"] += 1

            if examples["dls"] is None:
                examples["dls"] = match_id

        # -------------------------
        # Delivery-level cases
        # -------------------------

        match_has_super_over = False
        match_has_penalty = False
        match_has_non_boundary = False
        match_has_multi_wicket = False
        match_has_no_ball = False
        match_has_wide = False

        for innings in data.get("innings", []):

            if innings.get("super_over"):
                match_has_super_over = True

            for over in innings.get("overs", []):

                for delivery in over.get(
                    "deliveries",
                    []
                ):

                    extras = (
                        delivery.get("extras")
                        or {}
                    )

                    runs = (
                        delivery.get("runs")
                        or {}
                    )

                    wickets = (
                        delivery.get("wickets")
                        or []
                    )

                    if "penalty" in extras:
                        match_has_penalty = True

                    if runs.get(
                        "non_boundary"
                    ) is True:
                        match_has_non_boundary = True

                    if len(wickets) > 1:
                        match_has_multi_wicket = True

                    if "noballs" in extras:
                        match_has_no_ball = True

                    if "wides" in extras:
                        match_has_wide = True

        # -------------------------
        # Save match-level results
        # -------------------------

        if match_has_super_over:

            counts["super_over_matches"] += 1

            if examples["super_over"] is None:
                examples["super_over"] = match_id

        if match_has_penalty:

            counts["penalty_matches"] += 1

            if examples["penalty"] is None:
                examples["penalty"] = match_id

        if match_has_non_boundary:

            counts["non_boundary_matches"] += 1

            if examples["non_boundary"] is None:
                examples["non_boundary"] = match_id

        if match_has_multi_wicket:

            counts["multi_wicket_matches"] += 1

            if examples["multi_wicket"] is None:
                examples["multi_wicket"] = match_id

        if match_has_no_ball:

            counts["no_ball_matches"] += 1

            if examples["no_ball"] is None:
                examples["no_ball"] = match_id

        if match_has_wide:

            counts["wide_matches"] += 1

            if examples["wide"] is None:
                examples["wide"] = match_id

        # Progress every 500 matches.
        if index % 500 == 0:
            print(
                f"Processed {index}/{len(match_ids)}"
            )

    print("\n==============================")
    print("EDGE CASE SCAN")
    print("==============================")

    for key, value in counts.items():
        print(f"{key}: {value}")

    print("\n==============================")
    print("REPRESENTATIVE MATCHES")
    print("==============================")

    for key, value in examples.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()