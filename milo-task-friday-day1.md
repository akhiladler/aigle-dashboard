# Milo Task: Friday Day 1 Protocol

**Burden removed:** Akhil should not manually assemble Day 1 film fields from raw SAMS and Cinepoint evidence.

## When to Run
- Friday, after Cinepoint posts the week's Day 1 admissions and showtimes
- If one source is still missing, report the exact blocker and retry later

## Repo Scope
Use explicit dashboard repo scope only:
- `/root/aigle-dashboard`

Canonical files that matter:
- `operating_week.json`
- `weekly_state.json`
- `films.json`

## Goal
Produce a verified Day 1 update for the current operating-week films using:
- SAMS release-day numbers
- Cinepoint Day 1 numbers

Then update only the verified Day 1 fields in `films.json`.

## Friday Workflow

### Step 0: Preflight the live scope
Read:
- `operating_week.json`
- `weekly_state.json`

Confirm:
- `week_label`
- `week_start`
- `films_releasing`
- `ready_for_publish`

If `operating_week.json` and `weekly_state.json` disagree:
- emit `STATE_MISMATCH`
- include raw receipts
- do not continue

### Step 1: Capture raw evidence first
Collect raw evidence separately for:
- SAMS Day 1
- Cinepoint Day 1

Do not paraphrase.
Do not rewrite titles by hand if the raw source already has them.

#### SAMS preferred raw format
```text
Film Title | admissions | shows
```

or

```csv
title,admissions,shows
Film Title,245,34
```

#### Cinepoint raw format
Preserve the full raw blocks for:
- `ESTIMATED ADMISSION`
- `SHOWTIMES`

### Step 2: Parse SAMS Day 1
Run:

```bash
python /root/aigle-dashboard/parse_sams_day1.py --input <raw_sams_file> --release-date <YYYY-MM-DD>
```

Expected output:
- matched current-release films
- `day1_sams_adm`
- `day1_sams_shows`
- `day1_sams_adm_show`
- unmatched titles for review

Rules:
- never derive SAMS admissions from ratios
- never derive SAMS shows from ratios
- if the shows denominator is missing, leave all SAMS Day 1 fields blank and flag it

### Step 3: Parse Cinepoint Day 1
Run:

```bash
python /root/aigle-dashboard/parse_cinepoint_day1.py --input <raw_cinepoint_file> --release-date <YYYY-MM-DD>
```

Expected output:
- matched current-release films
- `day1_national_adm`
- `day1_national_screens`
- `day1_national_adm_show`
- unmatched or ambiguous titles for review

Rules:
- use Cinepoint only for raw Day 1 numbers
- if Cinepoint has not posted yet, report `BLOCKED | waiting_for_cinepoint`
- do not guess showtimes or ratios

### Step 4: Merge the two parsed sources
Run:

```bash
python /root/aigle-dashboard/merge_day1_sources.py --cinepoint <cinepoint_json> --sams <sams_json>
```

This is the Day 1 review packet.

### Step 5: Apply verified Day 1 fields to films.json
Run:

```bash
python /root/aigle-dashboard/apply_day1_merged.py --input <merged_json> --write
```

Update only:
- `day1_national_adm`
- `day1_national_screens`
- `day1_national_adm_show`
- `day1_sams_adm`
- `day1_sams_shows`
- `day1_sams_adm_show`

Do not touch unrelated films.
Do not touch non-Day 1 fields.

### Step 6: Validate before publish
Run:

```bash
python /root/aigle-dashboard/validate_films.py
python /root/aigle-dashboard/check-films.py
```

If validation fails:
- emit the exact blocker
- do not publish

### Step 7: Report to Akhil
Format:

```text
Day 1: [date]
[Film 1]: SAMS [adm]/[shows] = [ratio] | National [adm]/[screens] = [ratio]
[Film 2]: SAMS [adm]/[shows] = [ratio] | National [adm]/[screens] = [ratio]
Blocked:
- [exact missing source or ambiguity, if any]
```

Keep it short.
No speculative commentary.

## Escalate Instead Of Guessing

Escalate when:
- Cinepoint is not yet posted
- SAMS recap is incomplete
- a title match is ambiguous
- a ratio exists without a trustworthy denominator
- `operating_week.json` and `weekly_state.json` disagree

## Success Condition

Friday Day 1 is successful when:
- raw receipts exist
- parsed outputs match the live operating week
- only verified Day 1 fields are written
- validation passes
- Akhil receives a short receipt-based report
