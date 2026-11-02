import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MATCHES_DIR = PROJECT_ROOT / "data" / "raw" / "cricsheet" / "matches"


def load_match(file_path):
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_match(file_path):
    data = load_match(file_path)
    info = data.get("info", {})

    errors = []

    match_id = file_path.stem
    teams = info.get("teams", [])

    # Basic match validation
    if len(teams) != 2:
        errors.append("Match does not contain exactly two teams")

    if info.get("gender") != "male":
        errors.append("Match is not men's cricket")

    if info.get("match_type") not in {"T20", "IT20"}:
        errors.append("Match is not T20/IT20")

    innings_list = data.get("innings", [])

    if not innings_list:
        errors.append("No innings found")

    total_deliveries = 0

    for innings_number, innings in enumerate(
        innings_list,
        start=1
    ):
        batting_team = innings.get("team")

        if batting_team not in teams:
            errors.append(
                f"Innings {innings_number}: "
                f"batting team '{batting_team}' not in match teams"
            )

        innings_runs = 0

        previous_over = -1

        for over in innings.get("overs", []):
            over_number = over.get("over")

            if over_number is None:
                errors.append(
                    f"Innings {innings_number}: missing over number"
                )
                continue

            if over_number < previous_over:
                errors.append(
                    f"Innings {innings_number}: "
                    f"overs are not ordered"
                )

            previous_over = over_number

            for delivery in over.get("deliveries", []):
                total_deliveries += 1

                batter = delivery.get("batter")
                bowler = delivery.get("bowler")
                non_striker = delivery.get("non_striker")

                if not batter:
                    errors.append(
                        f"Innings {innings_number}: missing batter"
                    )

                if not bowler:
                    errors.append(
                        f"Innings {innings_number}: missing bowler"
                    )

                if not non_striker:
                    errors.append(
                        f"Innings {innings_number}: missing non-striker"
                    )

                runs = delivery.get("runs") or {}

                batter_runs = runs.get("batter", 0)
                extra_runs = runs.get("extras", 0)
                total_runs = runs.get("total", 0)

                if batter_runs < 0:
                    errors.append(
                        f"Innings {innings_number}: negative batter runs"
                    )

                if extra_runs < 0:
                    errors.append(
                        f"Innings {innings_number}: negative extra runs"
                    )

                if total_runs < 0:
                    errors.append(
                        f"Innings {innings_number}: negative total runs"
                    )

                if batter_runs + extra_runs != total_runs:
                    errors.append(
                        f"Innings {innings_number}: "
                        f"run components do not add up"
                    )

                innings_runs += total_runs

        if innings_runs < 0:
            errors.append(
                f"Innings {innings_number}: invalid innings total"
            )

    return {
        "match_id": match_id,
        "errors": errors,
        "total_deliveries": total_deliveries,
    }


def main():
    files = []

    for file_path in MATCHES_DIR.glob("*.json"):
        try:
            data = load_match(file_path)
        except Exception:
            continue

        info = data.get("info", {})

        if (
            info.get("gender") == "male"
            and info.get("match_type") in {"T20", "IT20"}
        ):
            files.append(file_path)

    print(f"Men's T20/IT20 matches found: {len(files)}")

    # Validate first 100 matches.
    sample = files[:100]

    print(f"Validating sample: {len(sample)} matches")

    valid_matches = 0
    invalid_matches = 0
    total_errors = 0
    total_deliveries = 0

    for index, file_path in enumerate(sample, start=1):
        result = validate_match(file_path)

        total_deliveries += result["total_deliveries"]

        if result["errors"]:
            invalid_matches += 1
            total_errors += len(result["errors"])

            print(f"\n❌ {result['match_id']}")

            for error in result["errors"][:10]:
                print(f"   - {error}")

        else:
            valid_matches += 1

        if index % 10 == 0:
            print(f"Processed {index}/{len(sample)}")

    print("\n==============================")
    print("VALIDATION SUMMARY")
    print("==============================")
    print(f"Matches tested:     {len(sample)}")
    print(f"Valid matches:      {valid_matches}")
    print(f"Invalid matches:    {invalid_matches}")
    print(f"Total errors:       {total_errors}")
    print(f"Total deliveries:   {total_deliveries}")


if __name__ == "__main__":
    main()