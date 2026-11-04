# Data Validation Report

## 1. Purpose

This document records the validation results for the canonical men's T20/IT20 dataset generated from Cricsheet JSON match files.

The purpose of validation is to ensure that the processed match, innings, and delivery datasets are structurally consistent, internally valid, and suitable for use by the Contextual Player Value Index (PVI) analytical engine.

---

## 2. Dataset Scope

The dataset contains men's T20 and IT20 matches extracted from the Cricsheet men's JSON archive.

| Dataset    |   Records |
| ---------- | --------: |
| Matches    |    11,017 |
| Innings    |    22,025 |
| Deliveries | 2,514,237 |

The processed datasets are:

- `data/processed/match_metadata.csv`
- `data/processed/innings.csv`
- `data/processed/deliveries.csv`

---

## 3. Overall Validation Result

The complete processed dataset was subjected to full validation.

| Validation Metric                 |    Result |
| --------------------------------- | --------: |
| Matches tested                    |    11,017 |
| Valid matches                     |    11,017 |
| Invalid matches                   |         0 |
| Total errors                      |         0 |
| Total warnings                    |         0 |
| Total deliveries                  | 2,514,237 |
| Legal deliveries                  | 2,418,780 |
| Wicket events                     |   138,084 |
| Wickets lost                      |   137,893 |
| Duplicate canonical delivery keys |         0 |

### Final Status

**PASS**

All 11,017 processed matches passed the validation checks.

There were:

- 0 invalid matches
- 0 validation errors
- 0 validation warnings
- 0 duplicate canonical delivery keys

---

## 4. Validation Checks

The validation process checks the following areas.

### 4.1 Match Structure

The validator checks that match-level information is present and structurally valid, including:

- Match ID
- Date
- Teams
- Competition
- Season
- Match type
- Gender
- Winner and result information where available

---

### 4.2 Innings Structure

The validator checks innings-level records for:

- Valid match references
- Valid innings numbering
- Batting team
- Bowling team
- Target information where applicable
- Innings totals
- Wickets lost
- Super-over information
- Innings ending information

---

### 4.3 Delivery Structure

Each delivery is checked for the expected canonical delivery fields, including:

- Match ID
- Innings number
- Over number
- Ball number
- Batter
- Bowler
- Non-striker
- Batting team
- Bowling team
- Runs
- Extras
- Legal-delivery status
- Wicket information

---

### 4.4 Delivery Ordering

Deliveries are checked to ensure that their canonical ordering is consistent within each innings.

The canonical delivery identity is:

```text
(match_id, innings_number, over_number, ball_number)
```
