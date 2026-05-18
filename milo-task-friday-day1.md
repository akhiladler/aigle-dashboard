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
- human-provided SAMS release-day numbers
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

Important:
- Milo may collect public Cinepoint Day 1 data on its own
- Milo may not invent or assume private SAMS Day 1 data
- if SAMS Day 1 is only available through operator channels, wait for Akhil to provide the raw SAMS block and treat that as the canonical internal input

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

Showtimes rule:
- prefer the official Cinepoint `SHOWTIMES` block for the national denominator
- do not derive the Friday national denominator from Cinepoint movie-detail pages unless that source is explicitly verified as equivalent
- if only admissions are available but the official `SHOWTIMES` block is missing, keep `day1_national_adm` and leave `day1_national_screens` / `day1_national_adm_show` blank

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
- do not treat a movie-detail page count as the official `SHOWTIMES` denominator unless separately verified

### Step 4: Merge the two parsed sources
Run:

```bash
python /root/aigle-dashboard/merge_day1_sources.py --cinepoint <cinepoint_json> --sams <sams_json>
```

This is the Day 1 review packet.

### Step 4.5: Standing Day 1 / Day 2 allocation read
Whenever SAMS Day 1 includes known show allocation, calculate an allocation table before making or summarizing Day 2 recommendations.

Required metrics for every title with known SAMS shows:
- `show_share = film_shows / total_known_shows`
- `admission_share = film_admissions / total_known_admissions_for_known_show_titles`
- `admissions_per_show = film_admissions / film_shows`
- `allocation_index = admission_share / show_share`

Denominator rule:
- titles with admissions but unknown show counts must be listed separately and must not enter the Allocation Index denominator.

Every allocation change or recommendation must be classified as exactly one of:
- `demand-led`
- `support/community-led`
- `site-led`
- `supply/distribution-led`
- `unknown`

Every Day 2 recommendation must cite the evidence it rests on:
- admissions/show
- Allocation Index
- site exceptions, if any
- operator rationale, if supplied

Output requirement:
- include the allocation table and one concise operator read; do not return only a table.

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
- SAMS Day 1 has not yet been provided by Akhil / operator channel
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

## Scope Truth

Friday has two different collection surfaces:
- public Cinepoint Day 1 can be cron-collected automatically
- private SAMS Day 1 still requires human handoff unless and until a safe internal feed exists

Do not confuse a successful public-data cron with a complete Friday Day 1 update.
