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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "sample"
)

MATCH_ID = "1082591"

SAMPLE_SIZE = 150

OUTPUT_FILE = (
    OUTPUT_DIR
    / f"deliveries_sample_{MATCH_ID}.csv"
)


COLUMNS = [
    "match_id",
    "innings_number",
    "over_number",
    "ball_number",
    "delivery_id",
    "batting_team",
    "bowling_team",
    "batter",
    "bowler",
    "non_striker",
    "runs_batter",
    "runs_extras",
    "runs_total",
    "runs_non_boundary",
    "is_legal_delivery",
    "extra_wides",
    "extra_noballs",
    "extra_byes",
    "extra_legbyes",
    "extra_penalty",
    "extra_other",
    "is_wicket",
    "wicket_events",
    "fielders_involved",
    "is_super_over",
]


def load_match(match_id):
    """Load one Cricsheet match JSON file."""

    match_file = MATCHES_DIR / f"{match_id}.json"

    if not match_file.exists():
        raise FileNotFoundError(
            f"Match file not found: {match_file}"
        )

    with match_file.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def parse_deliveries(data, match_id):
    """Parse deliveries using the canonical schema."""

    delivery_records = []

    teams = data["info"].get("teams", [])

    for innings_number, innings in enumerate(
        data.get("innings", []),
        start=1
    ):
        batting_team = innings.get("team")

        bowling_team = next(
            (
                team
                for team in teams
                if team != batting_team
            ),
            None
        )

        is_super_over = innings.get(
            "super_over",
            False
        )

        for over_data in innings.get(
            "overs",
            []
        ):
            over_number = over_data.get("over")

            for ball_number, delivery in enumerate(
                over_data.get("deliveries", []),
                start=1
            ):
                runs = delivery.get("runs") or {}
                extras = delivery.get("extras") or {}
                wickets = delivery.get("wickets") or []

                wide_runs = extras.get(
                    "wides",
                    0
                )

                no_ball_runs = extras.get(
                    "noballs",
                    0
                )

                bye_runs = extras.get(
                    "byes",
                    0
                )

                legbye_runs = extras.get(
                    "legbyes",
                    0
                )

                penalty_runs = extras.get(
                    "penalty",
                    0
                )

                known_extra_keys = {
                    "wides",
                    "noballs",
                    "byes",
                    "legbyes",
                    "penalty",
                }

                other_extra_runs = sum(
                    value
                    for key, value in extras.items()
                    if (
                        key not in known_extra_keys
                        and isinstance(
                            value,
                            (int, float)
                        )
                    )
                )

                is_legal_delivery = (
                    wide_runs == 0
                    and no_ball_runs == 0
                )

                runs_non_boundary = runs.get(
                    "non_boundary",
                    False
                )

                wicket_events = []

                for wicket in wickets:
                    fielders = []

                    for fielder in wicket.get(
                        "fielders",
                        []
                    ):
                        if isinstance(
                            fielder,
                            dict
                        ):
                            name = fielder.get(
                                "name"
                            )

                            if name:
                                fielders.append(
                                    name
                                )

                        elif isinstance(
                            fielder,
                            str
                        ):
                            fielders.append(
                                fielder
                            )

                    wicket_events.append({
                        "player_out": wicket.get(
                            "player_out"
                        ),
                        "kind": wicket.get(
                            "kind"
                        ),
                        "fielders": fielders,
                    })

                fielders_involved = []

                for event in wicket_events:
                    for fielder in event[
                        "fielders"
                    ]:
                        if fielder not in fielders_involved:
                            fielders_involved.append(
                                fielder
                            )

                record = {
                    "match_id": match_id,
                    "innings_number": innings_number,
                    "over_number": over_number,
                    "ball_number": ball_number,
                    "delivery_id": delivery.get(
                        "actual_delivery"
                    ),
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "batter": delivery.get(
                        "batter"
                    ),
                    "bowler": delivery.get(
                        "bowler"
                    ),
                    "non_striker": delivery.get(
                        "non_striker"
                    ),
                    "runs_batter": runs.get(
                        "batter",
                        0
                    ),
                    "runs_extras": runs.get(
                        "extras",
                        0
                    ),
                    "runs_total": runs.get(
                        "total",
                        0
                    ),
                    "runs_non_boundary": (
                        runs_non_boundary
                    ),
                    "is_legal_delivery": (
                        is_legal_delivery
                    ),
                    "extra_wides": wide_runs,
                    "extra_noballs": no_ball_runs,
                    "extra_byes": bye_runs,
                    "extra_legbyes": legbye_runs,
                    "extra_penalty": penalty_runs,
                    "extra_other": other_extra_runs,
                    "is_wicket": len(wickets) > 0,
                    "wicket_events": wicket_events,
                    "fielders_involved": (
                        fielders_involved
                    ),
                    "is_super_over": (
                        is_super_over
                    ),
                }

                delivery_records.append(record)

    return delivery_records


def serialize_complex_value(value):
    """
    Store lists/dictionaries safely inside CSV cells.
    """

    if isinstance(value, (list, dict)):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return value


def main():
    print(
        f"Loading match {MATCH_ID}..."
    )

    data = load_match(MATCH_ID)

    print("Parsing deliveries...")

    deliveries = parse_deliveries(
        data,
        MATCH_ID
    )

    print(
        f"Total deliveries available: "
        f"{len(deliveries)}"
    )

    if len(deliveries) < SAMPLE_SIZE:
        raise ValueError(
            f"Match contains only "
            f"{len(deliveries)} deliveries."
        )

    # Take the first 150 consecutive
    # deliveries from the match.
    sample = deliveries[:SAMPLE_SIZE]

    # Ensure output directory exists.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=COLUMNS
        )

        writer.writeheader()

        for record in sample:
            row = {
                column: serialize_complex_value(
                    record[column]
                )
                for column in COLUMNS
            }

            writer.writerow(row)

    # Sample statistics.
    extras_count = sum(
        1
        for record in sample
        if record["runs_extras"] > 0
    )

    wicket_count = sum(
        1
        for record in sample
        if record["is_wicket"]
    )

    non_boundary_count = sum(
        1
        for record in sample
        if record["runs_non_boundary"]
    )

    wide_count = sum(
        1
        for record in sample
        if record["extra_wides"] > 0
    )

    no_ball_count = sum(
        1
        for record in sample
        if record["extra_noballs"] > 0
    )

    print("\n" + "=" * 60)
    print("SAMPLE DATASET CREATED")
    print("=" * 60)

    print(
        f"Match ID: {MATCH_ID}"
    )

    print(
        f"Consecutive deliveries: "
        f"{len(sample)}"
    )

    print(
        f"Output file: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Deliveries containing extras: "
        f"{extras_count}"
    )

    print(
        f"Deliveries containing wickets: "
        f"{wicket_count}"
    )

    print(
        f"Non-boundary deliveries: "
        f"{non_boundary_count}"
    )

    print(
        f"Wide deliveries: "
        f"{wide_count}"
    )

    print(
        f"No-ball deliveries: "
        f"{no_ball_count}"
    )

    print(
        "\nFirst delivery:"
    )

    print(sample[0])

    print(
        "\nLast delivery:"
    )

    print(sample[-1])


if __name__ == "__main__":
    main()