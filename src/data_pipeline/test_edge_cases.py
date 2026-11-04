from pathlib import Path

from parser import (
    load_match,
    parse_match_metadata,
    parse_innings,
    parse_deliveries,
    validate_innings_totals,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATCHES_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "cricsheet"
    / "matches"
)


EDGE_CASES = {
    "super_over": "1023647",
    "dls": "1003861",
    "penalty": "1068309",
    "non_boundary": "1023631",
    "multi_wicket": "1130684",
    "no_ball": "1001349",
    "wide": "1001349",
}


def test_match(case_name, match_id):
    print("\n" + "=" * 70)
    print(f"{case_name.upper()} TEST — MATCH {match_id}")
    print("=" * 70)

    match_file = MATCHES_DIR / f"{match_id}.json"

    if not match_file.exists():
        print(f"ERROR: Match file not found: {match_file}")
        return False

    data = load_match(match_file)

    metadata = parse_match_metadata(
        data,
        match_id
    )

    innings = parse_innings(
        data,
        match_id
    )

    deliveries = parse_deliveries(
        data,
        match_id
    )

    validation = validate_innings_totals(
        data,
        deliveries
    )

    print("\nMatch metadata:")
    print(f"  Match ID: {metadata['match_id']}")
    print(f"  Date: {metadata['date']}")
    print(f"  Competition: {metadata['competition']}")
    print(
        f"  Teams: "
        f"{metadata['team_1']} vs {metadata['team_2']}"
    )
    print(f"  Winner: {metadata['winner']}")
    print(
        f"  Result status: "
        f"{metadata['result_status']}"
    )
    print(
        f"  Result method: "
        f"{metadata['result_method']}"
    )
    print(
        f"  Margin (runs): "
        f"{metadata['winning_margin_runs']}"
    )
    print(
        f"  Margin (wickets): "
        f"{metadata['winning_margin_wickets']}"
    )

    print("\nInnings:")

    for record in innings:
        print(
            f"  Innings {record['innings_number']}: "
            f"{record['batting_team']} "
            f"vs {record['bowling_team']}"
        )

        print(
            f"    Target: "
            f"{record['target_runs']} runs / "
            f"{record['target_overs']} overs"
        )

        print(
            f"    Super over: "
            f"{record['is_super_over']}"
        )

        print(
            f"    End reason: "
            f"{record['innings_end_reason']}"
        )

        print(
            f"    Total runs: "
            f"{record['total_runs']}"
        )

        print(
            f"    Total wickets: "
            f"{record['total_wickets']}"
        )

    print(
        f"\nTotal deliveries parsed: "
        f"{len(deliveries)}"
    )

    print("\nDetected edge cases:")

    has_super_over = any(
        record["is_super_over"]
        for record in innings
    )

    # D/L is determined from the match outcome method.
    # A normal chase also has target_runs/target_overs,
    # so target fields alone should not be treated as D/L.
    has_dls = (
        metadata["result_method"] == "D/L"
    )

    has_penalty = any(
        record["extra_penalty"] > 0
        for record in deliveries
    )

    has_non_boundary = any(
        record["runs_non_boundary"]
        for record in deliveries
    )

    has_multi_wicket = any(
        len(record["wicket_events"]) > 1
        for record in deliveries
    )

    has_no_ball = any(
        record["extra_noballs"] > 0
        for record in deliveries
    )

    has_wide = any(
        record["extra_wides"] > 0
        for record in deliveries
    )

    print(
        f"  Super over: "
        f"{has_super_over}"
    )

    print(
        f"  DLS/revised target: "
        f"{has_dls}"
    )

    print(
        f"  Penalty extra: "
        f"{has_penalty}"
    )

    print(
        f"  Non-boundary: "
        f"{has_non_boundary}"
    )

    print(
        f"  Multiple wickets: "
        f"{has_multi_wicket}"
    )

    print(
        f"  No-ball: "
        f"{has_no_ball}"
    )

    print(
        f"  Wide: "
        f"{has_wide}"
    )

    print("\nInnings total validation:")

    all_totals_match = True

    for result in validation:
        print(
            f"  Innings {result['innings_number']}: "
            f"expected={result['expected_runs']}, "
            f"parsed={result['parsed_runs']}, "
            f"match={result['runs_match']}"
        )

        if not result["runs_match"]:
            all_totals_match = False

    print("\nRelevant delivery examples:")

    if case_name == "penalty":
        examples = [
            d
            for d in deliveries
            if d["extra_penalty"] > 0
        ]

    elif case_name == "non_boundary":
        examples = [
            d
            for d in deliveries
            if d["runs_non_boundary"]
        ]

    elif case_name == "multi_wicket":
        examples = [
            d
            for d in deliveries
            if len(d["wicket_events"]) > 1
        ]

    elif case_name == "no_ball":
        examples = [
            d
            for d in deliveries
            if d["extra_noballs"] > 0
        ]

    elif case_name == "wide":
        examples = [
            d
            for d in deliveries
            if d["extra_wides"] > 0
        ]

    else:
        examples = []

    for delivery in examples[:3]:
        print(
            f"  delivery_id={delivery['delivery_id']}, "
            f"runs_total={delivery['runs_total']}, "
            f"extras={delivery['runs_extras']}, "
            f"wicket={delivery['is_wicket']}"
        )

        if delivery["wicket_events"]:
            print(
                f"    wicket_events="
                f"{delivery['wicket_events']}"
            )

        if delivery["fielders_involved"]:
            print(
                f"    fielders="
                f"{delivery['fielders_involved']}"
            )

    return all_totals_match


def main():
    results = {}

    for case_name, match_id in EDGE_CASES.items():
        results[case_name] = test_match(
            case_name,
            match_id
        )

    print("\n\n" + "=" * 70)
    print("EDGE-CASE PARSER TEST SUMMARY")
    print("=" * 70)

    passed = 0

    for case_name, result in results.items():
        status = "PASS" if result else "FAIL"

        print(
            f"{case_name:20} {status}"
        )

        if result:
            passed += 1

    print(
        f"\nPassed: "
        f"{passed}/{len(results)}"
    )


if __name__ == "__main__":
    main()