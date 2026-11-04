import json
from pathlib import Path


def load_match(file_path):
    """Load one Cricsheet JSON match file."""
    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_match_metadata(data, match_id):
    """Extract canonical match-level metadata."""
    info = data["info"]

    teams = info.get("teams", [])
    dates = info.get("dates", [])
    event = info.get("event") or {}
    outcome = info.get("outcome") or {}
    toss = info.get("toss") or {}

    # Determine result status.
    if outcome.get("winner"):
        result_status = "won"
    elif outcome.get("result"):
        result_status = outcome.get("result")
    else:
        result_status = None

    # Determine result method.
    result_method = outcome.get("method")

    # Determine winning margin.
    by = outcome.get("by") or {}

    winning_margin_runs = by.get("runs")
    winning_margin_wickets = by.get("wickets")

    return {
        "match_id": match_id,
        "date": dates[0] if dates else None,
        "competition": event.get("name"),
        "season": info.get("season"),
        "venue": info.get("venue"),
        "city": info.get("city"),
        "team_1": teams[0] if len(teams) > 0 else None,
        "team_2": teams[1] if len(teams) > 1 else None,
        "winner": outcome.get("winner"),

        "result_status": result_status,
        "result_method": result_method,
        "winning_margin_runs": winning_margin_runs,
        "winning_margin_wickets": winning_margin_wickets,

        "toss_winner": toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "match_type": info.get("match_type"),
        "gender": info.get("gender"),
    }


def parse_innings(data, match_id):
    """Extract canonical innings-level records."""
    innings_records = []

    teams = data["info"].get("teams", [])

    for innings_number, innings in enumerate(
        data.get("innings", []),
        start=1
    ):
        batting_team = innings.get("team")

        # The other team is the bowling team.
        bowling_team = next(
            (team for team in teams if team != batting_team),
            None
        )

        target = innings.get("target") or {}

        is_super_over = innings.get("super_over", False)

        # Preserve important innings-ending information.
        if innings.get("declared"):
            innings_end_reason = "declared"
        elif innings.get("forfeited"):
            innings_end_reason = "forfeited"
        else:
            innings_end_reason = None

        # Calculate innings totals from deliveries.
        total_runs = 0
        total_wickets = 0

        for over_data in innings.get("overs", []):
            for delivery in over_data.get("deliveries", []):
                runs = delivery.get("runs") or {}
                total_runs += runs.get("total", 0)

                wickets = delivery.get("wickets") or []

                # Preserve every wicket event in delivery-level
                # wicket_events, but count only actual dismissals
                # as wickets lost.
                for wicket in wickets:
                    wicket_kind = wicket.get("kind")

                    if wicket_kind != "retired hurt":
                        total_wickets += 1

        record = {
            "match_id": match_id,
            "innings_number": innings_number,
            "batting_team": batting_team,
            "bowling_team": bowling_team,

            "target_runs": target.get("runs"),
            "target_overs": target.get("overs"),

            "is_super_over": is_super_over,
            "innings_end_reason": innings_end_reason,

            "total_runs": total_runs,
            "total_wickets": total_wickets,
        }

        innings_records.append(record)

    return innings_records


def parse_deliveries(data, match_id):
    """Extract canonical ball-by-ball delivery records."""
    delivery_records = []

    teams = data["info"].get("teams", [])

    for innings_number, innings in enumerate(
        data.get("innings", []),
        start=1
    ):
        batting_team = innings.get("team")

        # The other team is the bowling team.
        bowling_team = next(
            (team for team in teams if team != batting_team),
            None
        )

        is_super_over = innings.get("super_over", False)

        for over_data in innings.get("overs", []):
            over_number = over_data.get("over")

            for ball_number, delivery in enumerate(
                over_data.get("deliveries", []),
                start=1
            ):
                runs = delivery.get("runs") or {}
                extras = delivery.get("extras") or {}
                wickets = delivery.get("wickets") or []

                # Standard Cricsheet extras.
                wide_runs = extras.get("wides", 0)
                no_ball_runs = extras.get("noballs", 0)
                bye_runs = extras.get("byes", 0)
                legbye_runs = extras.get("legbyes", 0)
                penalty_runs = extras.get("penalty", 0)

                # Preserve any future/unrecognised extra types.
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
                    if key not in known_extra_keys
                    and isinstance(value, (int, float))
                )

                # Wides and no-balls do not count as legal deliveries.
                is_legal_delivery = (
                    wide_runs == 0
                    and no_ball_runs == 0
                )

                # Preserve whether the runs were explicitly marked
                # as a non-boundary by Cricsheet.
                runs_non_boundary = runs.get(
                    "non_boundary",
                    False
                )

                # Preserve every wicket event.
                wicket_events = []

                for wicket in wickets:
                    fielders = []

                    for fielder in wicket.get("fielders", []):
                        if isinstance(fielder, dict):
                            name = fielder.get("name")

                            if name:
                                fielders.append(name)

                        elif isinstance(fielder, str):
                            fielders.append(fielder)

                    wicket_events.append({
                        "player_out": wicket.get("player_out"),
                        "kind": wicket.get("kind"),
                        "fielders": fielders,
                    })

                # Flatten all fielders involved in wickets.
                fielders_involved = []

                for event in wicket_events:
                    for fielder in event["fielders"]:
                        if fielder not in fielders_involved:
                            fielders_involved.append(fielder)

                record = {
                    "match_id": match_id,
                    "innings_number": innings_number,

                    # Cricsheet over numbers are zero-based.
                    "over_number": over_number,

                    # Sequence of deliveries within the over.
                    # This is NOT the legal-ball number.
                    "ball_number": ball_number,

                    # Cricsheet's actual delivery label, e.g. 0.1.
                    "delivery_id": delivery.get("actual_delivery"),

                    "batting_team": batting_team,
                    "bowling_team": bowling_team,

                    "batter": delivery.get("batter"),
                    "bowler": delivery.get("bowler"),
                    "non_striker": delivery.get("non_striker"),

                    "runs_batter": runs.get("batter", 0),
                    "runs_extras": runs.get("extras", 0),
                    "runs_total": runs.get("total", 0),
                    "runs_non_boundary": runs_non_boundary,

                    "is_legal_delivery": is_legal_delivery,

                    "extra_wides": wide_runs,
                    "extra_noballs": no_ball_runs,
                    "extra_byes": bye_runs,
                    "extra_legbyes": legbye_runs,
                    "extra_penalty": penalty_runs,
                    "extra_other": other_extra_runs,

                    "is_wicket": len(wickets) > 0,
                    "wicket_events": wicket_events,
                    "fielders_involved": fielders_involved,

                    "is_super_over": is_super_over,
                }

                delivery_records.append(record)

    return delivery_records


def validate_innings_totals(data, deliveries):
    """
    Validate that parsed delivery totals match
    the source Cricsheet delivery totals.
    """
    results = []

    for innings_number, innings in enumerate(
        data.get("innings", []),
        start=1
    ):
        expected_runs = 0

        for over in innings.get("overs", []):
            for delivery in over.get("deliveries", []):
                runs = delivery.get("runs") or {}
                expected_runs += runs.get("total", 0)

        parsed_runs = sum(
            record["runs_total"]
            for record in deliveries
            if record["innings_number"] == innings_number
        )

        results.append({
            "innings_number": innings_number,
            "expected_runs": expected_runs,
            "parsed_runs": parsed_runs,
            "runs_match": expected_runs == parsed_runs,
        })

    return results


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]

    match_file = (
        project_root
        / "data"
        / "raw"
        / "cricsheet"
        / "matches"
        / "1082591.json"
    )

    data = load_match(match_file)

    metadata = parse_match_metadata(
        data,
        match_file.stem
    )

    innings = parse_innings(
        data,
        match_file.stem
    )

    deliveries = parse_deliveries(
        data,
        match_file.stem
    )

    validation_results = validate_innings_totals(
        data,
        deliveries
    )

    print("Match metadata:")

    for key, value in metadata.items():
        print(f"{key}: {value}")

    print("\nInnings:")

    for record in innings:
        print(record)

    print(
        f"\nTotal deliveries: {len(deliveries)}"
    )

    print("\nFirst 5 deliveries:")

    for record in deliveries[:5]:
        print(record)

    print("\nValidation:")

    for result in validation_results:
        print(result)