# Contextual Player Value Index (PVI) Engine
# Data Dictionary

## 1. Purpose

This document defines the canonical schemas used by the data pipeline for the men's T20/IT20 dataset.

The data pipeline produces three processed CSV files:

- `data/processed/match_metadata.csv`
- `data/processed/innings.csv`
- `data/processed/deliveries.csv`

These schemas form the data contract between the data pipeline and the analytical/PVI engine.

---

## 2. Dataset Scope

The current canonical dataset contains:

| Metric | Value |
|---|---:|
| Men's T20/IT20 matches | 11,017 |
| Innings | 22,025 |
| Deliveries | 2,514,237 |
| Legal deliveries | 2,418,780 |

Raw source data is stored under:

`data/raw/cricsheet/matches/`

Generated processed datasets are stored under:

`data/processed/`

---

# 3. Match Metadata Schema

File:

`data/processed/match_metadata.csv`

Total columns: **17**

| Column | Type | Description |
|---|---|---|
| `match_id` | string | Unique Cricsheet match identifier. |
| `date` | string/date | Match date. |
| `competition` | string | Competition or tournament name when available. |
| `season` | string | Competition season/year when available. |
| `venue` | string | Match venue when available. |
| `city` | string | Match city when available. |
| `team_1` | string | First team listed in the match metadata. |
| `team_2` | string | Second team listed in the match metadata. |
| `winner` | string | Winning team when the match has a recorded winner. |
| `result_status` | string | Result status from Cricsheet outcome information, such as `won` or another recorded result status. |
| `result_method` | string | Match result method when supplied by Cricsheet, such as `D/L`. |
| `winning_margin_runs` | integer | Winning margin in runs when applicable. |
| `winning_margin_wickets` | integer | Winning margin in wickets when applicable. |
| `toss_winner` | string | Team that won the toss. |
| `toss_decision` | string | Toss decision, such as `bat` or `field`. |
| `match_type` | string | Match type. The canonical dataset contains `T20` and `IT20`. |
| `gender` | string | Gender of the match. The canonical dataset contains men's matches. |

### Match-level notes

- `match_id` is the match-level identifier.
- `winner` may be empty/null when there is no recorded winning team.
- Run and wicket margin fields are applicable only when that type of margin exists.
- `result_method` preserves the source result method; for example, D/L matches are represented using the source method.
- `team_1` and `team_2` preserve the canonical ordering produced by the parser.

---

# 4. Innings Schema

File:

`data/processed/innings.csv`

Total columns: **10**

| Column | Type | Description |
|---|---|---|
| `match_id` | string | Match identifier linking the innings to `match_metadata.csv`. |
| `innings_number` | integer | Sequential innings number within the match. |
| `batting_team` | string | Team batting during the innings. |
| `bowling_team` | string | Team bowling during the innings. |
| `target_runs` | integer/null | Target score when a target is defined for the innings. |
| `target_overs` | number/null | Target number of overs when a target is defined. |
| `is_super_over` | boolean | Indicates whether the innings is a super-over innings. |
| `innings_end_reason` | string/null | Recorded innings end reason when available, such as `declared` or `forfeited`. |
| `total_runs` | integer | Total runs scored in the innings. |
| `total_wickets` | integer | Number of wickets lost according to the canonical parser's wicket-counting rules. |

### Innings notes

- `innings_number` is used together with `match_id` to uniquely identify an innings.
- The canonical dataset contains **0 duplicate `(match_id, innings_number)` pairs**.
- `target_runs` and `target_overs` are nullable because not every innings has a target.
- Super-over innings are explicitly identified using `is_super_over`.
- `innings_end_reason` preserves recognized source-level end conditions.

---

# 5. Delivery Schema

File:

`data/processed/deliveries.csv`

Total columns: **26**

| Column | Type | Description |
|---|---|---|
| `match_id` | string | Match identifier. |
| `innings_number` | integer | Innings containing the delivery. |
| `over_number` | integer | Zero-based over number from the Cricsheet source. |
| `ball_number` | integer | Delivery sequence within the over. This is the canonical sequence number, including deliveries that are wides or no-balls. |
| `delivery_id` | string | Source `actual_delivery` label from Cricsheet, for example `0.1`. |
| `batting_team` | string | Team batting on the delivery. |
| `bowling_team` | string | Team bowling on the delivery. |
| `batter` | string | Batter who faced the delivery. |
| `bowler` | string | Bowler who delivered the ball. |
| `non_striker` | string | Non-striker at the time of the delivery. |
| `runs_batter` | integer | Runs credited to the batter. |
| `runs_extras` | integer | Runs resulting from extras. |
| `runs_total` | integer | Total runs scored from the delivery. |
| `runs_non_boundary` | boolean | Indicates whether the delivery's runs are marked as non-boundary runs in the source data. |
| `is_legal_delivery` | boolean | Whether the delivery counts as a legal ball under the canonical rule. |
| `extra_wides` | integer | Runs recorded as wides. |
| `extra_noballs` | integer | Runs recorded as no-balls. |
| `extra_byes` | integer | Runs recorded as byes. |
| `extra_legbyes` | integer | Runs recorded as leg-byes. |
| `extra_penalty` | integer | Runs recorded as penalty runs. |
| `extra_other` | integer | Sum of numeric extra fields not represented by the standard extra columns. |
| `is_wicket` | boolean | Indicates whether the delivery contains one or more wicket events. |
| `wicket_events` | JSON string/list | Serialized list of wicket-event dictionaries, preserving all source wicket events. |
| `fielders_involved` | JSON string/list | Flattened unique list of fielders involved in wicket events. |
| `is_super_over` | boolean | Indicates whether the delivery belongs to a super-over innings. |

---

# 6. Delivery Identity and Ordering

## Canonical delivery key

The unique delivery identity is:

```text
(match_id, innings_number, over_number, ball_number)
```

The full dataset was validated using this canonical key and contains:

```text
Duplicate canonical delivery keys: 0
```

## `delivery_id` / `actual_delivery`

The `delivery_id` column stores Cricsheet's source `actual_delivery` value.

Example:

```text
0.1
0.2
0.3
```

**Important:** `delivery_id` is NOT the unique key for a delivery.

Cricsheet can use the same `actual_delivery` label for multiple source delivery records around wides and no-balls. Therefore, downstream analytical code must not use `delivery_id` alone as a primary key.

Use:

```text
match_id
+ innings_number
+ over_number
+ ball_number
```

for unique delivery identification.

---

# 7. Legal Delivery Definition

The canonical parser defines a delivery as legal when:

```text
wide_runs == 0
AND
no_ball_runs == 0
```

Therefore:

```text
is_legal_delivery = True
```

when the delivery is neither a wide nor a no-ball.

A wide or no-ball remains a delivery record and retains its position in the source delivery sequence, but it does not increment the legal-ball count.

Full dataset result:

```text
Total deliveries: 2514237
Legal deliveries: 2418780
```

---

# 8. Extras Handling

The canonical delivery schema separates common extra categories:

- `extra_wides`
- `extra_noballs`
- `extra_byes`
- `extra_legbyes`
- `extra_penalty`

The parser also provides:

`extra_other`

This is intended to preserve numeric extra values whose source keys are not represented by the standard columns.

The validation pipeline checks that the categorized extra values agree with the source `runs.extras` value.

---

# 9. Runs Handling

For every delivery:

```text
runs_batter + runs_extras = runs_total
```

The validation pipeline checks this relationship across the full canonical dataset.

Negative batter runs, negative extras, and negative total runs are treated as invalid records.

---

# 10. Wicket Handling

A delivery may contain one or more wicket events.

The `wicket_events` field preserves the source event information, including:

- `player_out`
- `kind`
- `fielders`

The `fielders_involved` field contains flattened unique fielder names from the wicket events.

The validator records wicket-event types including:

- `bowled`
- `caught`
- `caught and bowled`
- `handled the ball`
- `hit the ball twice`
- `hit wicket`
- `lbw`
- `obstructing the field`
- `retired hurt`
- `retired not out`
- `retired out`
- `run out`
- `stumped`

## Wicket events vs wickets lost

These are not always identical.

`wicket_events` represents recorded wicket events.

`total_wickets` / `wickets_lost` represents wickets counted as lost under the canonical parser's rules.

In particular:

```text
retired hurt
```

is preserved as a wicket event but is not counted as a wicket lost.

This distinction should be preserved when building analytical features.

---

# 11. Super Overs

Super-over information is explicitly retained.

At innings level:

```text
is_super_over
```

At delivery level:

```text
is_super_over
```

This allows analytical code to exclude or separately analyze super-over deliveries when required.

---

# 12. Data Validation Status

The complete men's T20/IT20 dataset was validated after the final validator correction.

Validation result:

```text
Matches tested:          11017
Valid matches:           11017
Invalid matches:         0
Total errors:            0
Total warnings:          0
Total deliveries:        2514237
Legal deliveries:        2418780
Wicket events:           138084
Wickets lost:            137893
Duplicate delivery keys: 0
```

Therefore, the current canonical dataset passes the implemented validation checks with zero errors, zero warnings, and zero duplicate canonical delivery keys.

---

# 13. Recommended Usage by the PVI Engine

The analytical engine should generally use:

### Match-level analysis

`match_metadata.csv`

Use for:

- match identification
- competition
- season
- teams
- winner
- venue/city
- toss information
- result information

### Innings-level analysis

`innings.csv`

Use for:

- innings context
- batting/bowling teams
- target information
- innings totals
- wickets lost
- super-over identification

### Ball-level analysis

`deliveries.csv`

Use for:

- batter/bowler actions
- runs
- extras
- legal-ball state
- wickets
- match situation
- ball-by-ball feature engineering
- player contribution calculations

---

# 14. Data Relationship

The three datasets are related as follows:

```text
match_metadata
      |
      | match_id
      v
innings
      |
      | match_id + innings_number
      v
deliveries
```

Primary analytical relationships:

```text
match_metadata.match_id
        ↓
innings.match_id

innings.(match_id, innings_number)
        ↓
deliveries.(match_id, innings_number)
```

---

# 15. Important Data Contract Rules

The following rules should be treated as part of the stable data contract:

1. Do not treat `delivery_id` / `actual_delivery` as globally unique.
2. Use `(match_id, innings_number, over_number, ball_number)` as the canonical delivery key.
3. Do not remove wide/no-ball records from the dataset merely because they are not legal deliveries.
4. Use `is_legal_delivery` when calculating legal-ball counts.
5. Preserve wicket events even when the event does not represent a wicket lost, such as `retired hurt`.
6. Preserve `wicket_events` as structured information rather than reducing it to only a boolean.
7. Preserve extras by category.
8. Use `runs_total` for total delivery runs and `runs_batter` for batter-attributed runs.
9. Treat nullable match/innings fields as potentially unavailable source information rather than automatically assuming zero.
10. Keep super-over records identifiable using `is_super_over`.

---

# 16. Processed Files

The canonical processed files are:

```text
data/
├── processed/
│   ├── match_metadata.csv
│   ├── innings.csv
│   └── deliveries.csv
└── sample/
    └── deliveries_sample_1082591.csv
```

The sample file contains 150 consecutive deliveries from match `1082591` and uses the same delivery schema documented above.
