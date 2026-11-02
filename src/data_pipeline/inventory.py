import csv
import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATCHES_DIR = PROJECT_ROOT / "data" / "raw" / "cricsheet" / "matches"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "match_metadata.csv"


def main():
    files = list(MATCHES_DIR.glob("*.json"))

    print(f"Total JSON files found: {len(files)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    match_type_counts = Counter()
    t20_count = 0

    for index, file_path in enumerate(files, start=1):

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        info = data["info"]

        match_type = info.get("match_type")
        gender = info.get("gender")

        match_type_counts[match_type] += 1

        teams = info.get("teams", [])
        event = info.get("event") or {}
        dates = info.get("dates", [])
        outcome = info.get("outcome") or {}
        toss = info.get("toss") or {}

        row = {
            "match_id": file_path.stem,
            "gender": gender,
            "match_type": match_type,
            "team_type": info.get("team_type"),
            "competition": event.get("name"),
            "season": info.get("season"),
            "date": dates[0] if dates else None,
            "team_1": teams[0] if len(teams) > 0 else None,
            "team_2": teams[1] if len(teams) > 1 else None,
            "venue": info.get("venue"),
            "city": info.get("city"),
            "winner": outcome.get("winner"),
            "toss_winner": toss.get("winner"),
            "toss_decision": toss.get("decision"),
        }

        rows.append(row)

        if gender == "male" and match_type in {"T20", "IT20"}:
            t20_count += 1

        if index % 1000 == 0:
            print(f"Processed {index}/{len(files)} files...")

    fieldnames = [
        "match_id",
        "gender",
        "match_type",
        "team_type",
        "competition",
        "season",
        "date",
        "team_1",
        "team_2",
        "venue",
        "city",
        "winner",
        "toss_winner",
        "toss_decision",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

    print("\n=== MATCH TYPE COUNTS ===")

    for match_type, count in match_type_counts.most_common():
        print(f"{match_type}: {count}")

    print("\n=== MEN'S T20 COUNT ===")
    print(t20_count)

    print(f"\nMetadata CSV created:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()