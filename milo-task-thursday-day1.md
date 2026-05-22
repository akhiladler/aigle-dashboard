# Milo Task: Thursday Night Provisional Day 1

## Purpose
Day 2 schedules are often made Thursday night. Friday morning can be too late.

Every Thursday release day, produce a provisional private SAMS Day 1 read when Grafana data is available.

Status label: `PROVISIONAL_DAY1_NIGHT`

This is not the final Friday Day 1 close. The business day may still be incomplete.

## Repo Scope
Use explicit dashboard repo scope only:
- `/root/aigle-dashboard`

Canonical files that matter:
- `operating_week.json`
- `weekly_state.json`
- `films.json` for prerelease signals / Decision Card context only

Read-only rule:
- Do not mutate files.
- Do not commit.
- Do not POST to Sheet.
- Do not write business data.

## Trigger Window
Run every Thursday release day around 21:30-22:30 WIB.

Goal:
- give Akhil / programming a provisional Day 2 allocation read before Friday morning
- reduce the chance that Day 2 scheduling decisions happen before Aigle sees private SAMS evidence

## Step 0: Preflight live scope
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

## Step 1: Bounded Grafana read
Use the dedicated read-only SAMS Grafana account as private SAMS truth when accessible.

Read scope:
- date: current `operating_week.week_start` / Thursday release day
- titles: current operating slate
- holdovers: relevant holdovers competing for Day 2 allocation
- distortion titles: known distortion titles such as NOBAR or community-event titles if they affect allocation pressure
- fields: movie title, actual show count, admissions / adm seats, paid seats if visible, voucher/freepass seats if visible, report date/time, cinema/site filter state
- source area: Movie Programing / BO Sales / Admission or equivalent admission + showtime report only

Privacy limits:
- use read-only access only
- do not open edit/admin/settings pages
- do not extract credentials, customer lists, staff data, payment rows, revenue details, F&B data, or unrelated operational data
- do not store screenshots or raw dashboard dumps unless Akhil explicitly requests them for audit
- if unrelated private data is visible outside this scope, stop and return `BLOCKED_GRAFANA_EXTRACTION | unrelated_private_data_visible`

If Grafana fails:
- return `BLOCKED_GRAFANA_ACCESS | <exact reason>` for login, permission, network, session, MFA, or dashboard access failure
- return `BLOCKED_GRAFANA_EXTRACTION | <exact reason>` if the dashboard loads but scoped titles/date/admissions/show counts cannot be extracted safely
- do not ask for manual paste unless the Grafana blocker is reported first

## Step 2: Planned vs actual show counts
Distinguish planned allocation from actual Day 1 shows.

Definitions:
- planned allocation = programming intent / schedule plan before or during release day
- actual Day 1 shows = count of Grafana scheduled showtime rows that actually belong to the scoped title/date/site, filtered to valid playing/approved rows when visible

Rules:
- use actual Day 1 shows as the denominator for admissions/show
- use planned allocation only as context for planned-vs-actual variance
- do not use planned allocation as the performance denominator when actual Grafana show counts are available
- if planned allocation is missing, still calculate actual-show ratios from Grafana and mark planned variance as unavailable

## Step 3: Calculate provisional allocation metrics
For every scoped title with private SAMS admissions and actual show count, calculate:
- `show_share = actual_day1_shows / total_actual_day1_shows_for_known_show_titles`
- `admission_share = admissions / total_admissions_for_known_show_titles`
- `admissions_per_show = admissions / actual_day1_shows`
- `market_average_admissions_per_show = total_admissions_for_known_show_titles / total_actual_day1_shows_for_known_show_titles`
- `allocation_index = admission_share / show_share`

Denominator rules:
- include relevant holdovers when they compete for Day 2 screens and have known admissions/show counts
- include known distortion titles when they affect allocation pressure, but label the distortion clearly
- treat NOBAR/community-event titles as distortion unless ordinary demand is separately proven
- titles with admissions but unknown actual show counts must be listed separately and excluded from Allocation Index denominators

## Step 4: Decision Card thesis test
For every current-slate title with a pre-admissions Decision Card:
- test the original thesis against provisional Day 1 evidence
- classify exactly one of: `thesis passed`, `thesis failed`, `inconclusive`
- cite admissions/show, market average, Allocation Index, and the card's stated success/failure test when available

If the original Decision Card is missing:
- create a minimal retro-card from available prerelease evidence
- mark confidence `low`
- do not skip thesis testing silently

## Step 5: Provisional Day 2 recommendation
Produce one concise provisional Day 2 recommendation.

Classify each title exactly one of:
- `protect`
- `increase`
- `hold`
- `reduce`
- `cut`
- `support-only`
- `site-exception`

Every recommendation must cite:
- admissions/show
- market average admissions/show
- Allocation Index
- planned vs actual show count distinction when it matters
- comparison against important holdovers
- distortion flags such as NOBAR, if relevant
- operator rationale, if supplied

Do not overclaim:
- label the read `PROVISIONAL_DAY1_NIGHT`
- state that the business day may still be incomplete
- keep public Cinepoint separate; do not use public Cinepoint numbers as private SAMS truth
- do not call the read final

## Step 6: Optional operator-facing message
Label exactly one of:
- `SEND`
- `DO_NOT_SEND`

Use `SEND` only if the provisional message would materially help Day 2 scheduling discipline before the final Friday read.

If `SEND`, draft a short operator-language message covering:
- which titles to protect / reduce
- admissions/show vs market average
- planned vs actual show distinction only if relevant
- distortion warning only if it changes the decision

If `DO_NOT_SEND`, provide no draft.

## Output Contract
Return:
- `PROVISIONAL_DAY1_NIGHT`
- private SAMS Day 1 table
- planned vs actual show count distinction
- admissions/show
- market average admissions/show
- Allocation Index
- Decision Card thesis pass/fail/inconclusive
- provisional Day 2 recommendation
- optional operator message labeled `SEND` or `DO_NOT_SEND`
- blockers / caveats

## Success Condition
Thursday night provisional Day 1 is successful when:
- Grafana private SAMS read is bounded and scoped
- current operating slate and relevant holdovers are included
- actual Day 1 shows are distinguished from planned allocation
- admissions/show, market average, and Allocation Index are calculated
- Decision Card theses are tested
- Day 2 provisional recommendation is produced
- output is labeled `PROVISIONAL_DAY1_NIGHT`
- no files, Sheet rows, or business data are mutated
