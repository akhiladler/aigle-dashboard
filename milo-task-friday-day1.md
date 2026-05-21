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
Produce a verified Day 1 update and Day 2 allocation read for the current operating-week films using:
- known SAMS show allocation
- Wednesday prerelease signals
- human-provided SAMS release-day admissions
- Cinepoint Day 1 numbers

Then update only the verified Day 1 fields in `films.json`.

Standing rule:
- before Day 1 admissions arrive, prepare the allocation framework from known show allocation and prerelease signals
- if show allocation is missing, return `BLOCKED_SHOW_ALLOCATION_MISSING`
- once Day 1 admissions arrive, calculate the full allocation table and one concise Day 2 operator read
- do not call Friday complete if private SAMS admissions or private SAMS show counts are missing

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
- SAMS show allocation
- SAMS Day 1
- Cinepoint Day 1

Do not paraphrase.
Do not rewrite titles by hand if the raw source already has them.

Important:
- Milo may collect public Cinepoint Day 1 data on its own
- Milo may not invent or assume private SAMS Day 1 data
- Milo may not invent or assume SAMS show allocation
- if SAMS Day 1 is only available through operator channels, wait for Akhil to provide the raw SAMS block and treat that as the canonical internal input

#### SAMS show allocation raw format
Before admissions arrive, capture known show allocation in this format:

```csv
title,shows
Film Title,34
```

If Day 2 planned allocation is already known, use:

```csv
title,day1_shows,day2_shows
Film Title,34,40
```

If show allocation is missing for the titles being evaluated, return:

```text
BLOCKED_SHOW_ALLOCATION_MISSING
```

Do not replace missing show allocation with guesses, ratios, national screens, or previous-week counts.

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

### Step 1.5: Pre-admissions allocation prep
Before private SAMS Day 1 admissions arrive, prepare a draft allocation frame using known SAMS show allocation and the current prerelease read.

Include:
- current operating-week new titles
- important holdovers still allocated
- show counts / show share for every title with known shows
- prerelease signal summary: YouTube, TikTok, Google Trends, PH tier, genre, and source-conflict notes
- holdover benchmark notes, especially titles with live WOM or operator-confirmed momentum
- an Aigle v2 preliminary allocation read for every relevant title

Aigle v2 decision rule:
- Do not only rank public buzz from YouTube, TikTok, and Google Trends.
- Decide what SAMS should protect, test, cut, or classify as support by combining public signals with SAMS fit, operator context, supply reality, and early allocation/performance when available.
- Classify every relevant title as exactly one of: `protect`, `test big`, `watch closely`, `test small`, `support-only`, `site-exception`, `cut candidate`, `unknown`.
- Every classification must cite evidence from the relevant signal families: awareness, intent, SAMS fit, distribution/supply, operator/organic read, special flags, and early allocation/performance if available.
- If a signal family is unknown or unavailable, say so; do not guess admissions, DCP availability, site rationale, or operator intent.

Rules:
- compare new titles against important holdovers, not only against each other
- if any title has admissions but unknown show count later, exclude it from Allocation Index denominators and list it separately
- if no trustworthy SAMS show allocation is available, return `BLOCKED_SHOW_ALLOCATION_MISSING`
- this pre-admissions prep is not Friday completion; it is a setup for Day 1 → Day 2 allocation

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
Whenever SAMS Day 1 includes private admissions and known show allocation, calculate an allocation table before making or summarizing Day 2 recommendations.

Required metrics for every title with known SAMS shows:
- `show_share = film_shows / total_known_shows`
- `admission_share = film_admissions / total_known_admissions_for_known_show_titles`
- `admissions_per_show = film_admissions / film_shows`
- `market_average_admissions_per_show = total_known_admissions_for_known_show_titles / total_known_shows`
- `allocation_index = admission_share / show_share`
- `verdict = over-allocated / fair / under-allocated / support-only / unknown`, based on Allocation Index, admissions/show, prerelease signal, and operator rationale

Denominator rule:
- titles with admissions but unknown show counts must be listed separately and must not enter the Allocation Index denominator.
- holdovers still allocated must be included when their admissions and show counts are known; do not evaluate new titles in isolation if holdovers are competing for screens.
- if private SAMS admissions are missing, return `BLOCKED_PRIVATE_SAMS_DAY1_MISSING` and do not call Friday complete.
- if private SAMS show counts are missing, return `BLOCKED_SHOW_ALLOCATION_MISSING` and do not call Friday complete.

Every allocation change or recommendation must be classified as exactly one of:
- `demand-led`
- `support/community-led`
- `site-led`
- `supply/distribution-led`
- `unknown`

Every Day 2 recommendation must cite the evidence it rests on:
- admissions/show
- market average admissions/show
- Allocation Index
- comparison against important holdovers
- site exceptions, if any
- operator rationale, if supplied

Output requirement:
- include the allocation table and one concise Day 2 operator read; do not return only a table.
- if the evidence is incomplete, return the exact blocker instead of a recommendation.

### Step 4.6: Optional operator-facing message draft
Every Friday, prepare one optional operator-facing Day 1 evaluation message only if it adds value.

Label the draft exactly one of:
- `SEND`
- `DO_NOT_SEND`

Use `SEND` only when the message gives Dias useful decision discipline he does not already have from the raw numbers. Use `DO_NOT_SEND` when it would be redundant, premature, blocked, or over-explaining.

The message, when drafted, should briefly explain the Day 1 evaluation frame in operator language:
- show share vs admission share
- admissions/show
- Allocation Index
- whether allocation looks `demand-led` or `support/community-led` when those labels are supported by evidence

Rules:
- do not ask Dias for unnecessary extra input
- do not over-water the plant
- do not assume the message should be sent
- Akhil decides whether to send

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
- SAMS show allocation is missing
- SAMS recap is incomplete
- a title match is ambiguous
- a ratio exists without a trustworthy denominator
- `operating_week.json` and `weekly_state.json` disagree

## Success Condition

Friday Day 1 is successful when:
- raw receipts exist
- parsed outputs match the live operating week
- private SAMS admissions and show counts exist for evaluated titles
- the Day 1 / Day 2 allocation table is calculated
- one concise Day 2 operator read is produced
- only verified Day 1 fields are written
- validation passes
- Akhil receives a short receipt-based report

## Scope Truth

Friday has two different collection surfaces:
- public Cinepoint Day 1 can be cron-collected automatically
- private SAMS Day 1 still requires human handoff unless and until a safe internal feed exists

Do not confuse a successful public-data cron with a complete Friday Day 1 update.
