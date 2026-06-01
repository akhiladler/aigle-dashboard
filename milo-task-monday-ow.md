# Milo Task: Monday First-Four/Five-Day Closeout

**Burden removed:** Akhil should not manually reconstruct the weekly learning loop from scattered prerelease, Day 1, allocation, SAMS, and Cinepoint evidence.

## When To Run

Monday after weekend / opening-frame evidence is available.

## Repo Scope

Use explicit dashboard repo scope only:
- `/root/aigle-dashboard`

Canonical files:
- `operating_week.json`
- `weekly_state.json`
- `films.json`
- `films_schedule.json`

## Goal

Close the release loop:

`prerelease read -> Day 1 -> Day 2 allocation -> opening frame -> lesson`

This is not just OW collection. OW collection is only one input.

## Step 0: Live-State Preflight

Read and report:
- repo path
- local commit
- origin/master commit
- dirty status
- `operating_week.week_label`
- `operating_week.week_start`
- `operating_week.films_releasing`

If local and origin disagree, emit `LOCAL_ONLY_CHANGE` or `STALE_REPO`.

If `operating_week.json` and `weekly_state.json` disagree, emit `STATE_MISMATCH`.

Do not continue from stale or contradictory state.

## Step 1: Separate Public And Private Layers

Keep layers separate until labeled:
- Cinepoint/public national data
- SAMS/private operator data

Do not mix public Cinepoint and private SAMS numbers in one denominator.

When SAMS Labuan Bajo (`LBJ`) is visible, report private SAMS totals through
three explicit lenses:
- `SAMS_OWNED`: exclude LBJ because it is a franchise site and SAMS does not
  own its revenue
- `SAMS_NETWORK_INCLUDING_LBJ`: include LBJ as SAMS brand-network activity
- `FRANCHISE_DELTA`: LBJ only

Keep ADM, paid seats, and revenue distinct. Treat `ADM > paid seats` as a
promo-distortion signal only. Do not infer BOGOF or another program solely from
the gap without operator context.

Before emitting `BLOCKED_PRIVATE_SAMS_OPENING_FRAME_MISSING`, attempt a bounded read-only Grafana extraction for private SAMS first-four-days / opening-frame data.

Proven Movie Programing BO route (primary as of 2026-05-23):
- Dashboard: Movie Programing (`/d/fe67op4i87myoa/movie-programing`).
- Method: set date + movie title filters and extract title-by-title from the `$movie - $date` table panel.
- Scope: all visible SAMS cinema rows; do not exclude Labuan Bajo or any other site unless explicitly instructed. Report observed site scope.
- Safe fields: Movie, Cinema, Studio, Showtime Date, Showtime Start, Ticket Price, Status/Aproval when visible, Total Amount, Adm Seats, Paid Seats, Voucher/Freepass if visible.
- Required labels: `grafana_paid_seats`, `grafana_adm_seats`, `grafana_total_amount`, `show_count`, `abdu_comparable_status = unverified_until_reconciled`.
- Keep paid seats and adm seats separate. Do not label either as Abdu Total Seat Sold before reconciliation.
- Never use Customer Transaction rows. Use Daily Report only for isolated aggregate site/BO totals if safe.

Grafana read scope:
- current operating slate
- relevant holdovers competing for allocation
- known distortion titles such as NOBAR/community-event titles when they affect allocation pressure
- fields needed only for closeout: title, date/frame, `grafana_paid_seats`, `grafana_adm_seats`, `grafana_total_amount`, actual show counts when visible, site/filter state, observed site scope, and report timestamp

If Grafana access fails, emit:

`BLOCKED_GRAFANA_ACCESS | <exact reason>`

If Grafana loads but extraction is unsafe or incomplete, emit:

`BLOCKED_GRAFANA_EXTRACTION | <exact reason>`

Only after Grafana failed and no valid manual fallback table is supplied, emit:

`BLOCKED_PRIVATE_SAMS_OPENING_FRAME_MISSING`

Then still report what public data is available, but do not call the week closed.

## Step 2: Opening-Frame Label

Label private SAMS data by timing and completeness:
- `FINAL_DAY1` = complete release-day private SAMS Day 1 after business day close
- `PROVISIONAL` = incomplete/private read before business day close or before final reconciliation
- `OPENING_FRAME` = first-four/five-day private SAMS frame used for Monday closeout

Derive `D1` from each title's actual release date. Do not assume a permanent
weekday. Label the frame with explicit dates and day count:
- always report `D1-D4` when the four-day window is complete
- if Monday includes additional evidence through Sunday, report
  `OPENING_FRAME_TO_SUNDAY` separately
- Thursday release example: `D1-D4 = Thu-Sun`
- Wednesday release example: `D1-D4 = Wed-Sat`,
  `OPENING_FRAME_TO_SUNDAY = D1-D5 = Wed-Sun`
- if titles in the same closeout have different release dates, separate cohorts

Never compare a Wednesday-to-Sunday 5-day frame blindly with a normal Thursday-to-Sunday 4-day OW.

For the May 27, 2026 cohort, `Cyberbullying` is operator-confirmed NOBAR.
Report it as `DISTORTION_CONTEXT`; exclude it from clean ordinary-demand
denominators unless an operator explicitly asks for a separate NOBAR view.

## Step 3: Cinepoint Revision Check

Keep public Cinepoint separate from private SAMS. Do not mix public national data and private SAMS data in one denominator.

If Cinepoint posts next-day cumulative and current-day daily admissions:

`revised Day 1 = cumulative - current-day daily`

Use this over earlier opening estimates when both refer to the same release run.

If revision changes prior Sheet/dashboard values, report the arithmetic receipt before recommending corrections.

## Step 4: Day 2 Allocation Context

If SAMS Day 1 admissions and show allocation exist, include the Day 2 allocation read:
- show share
- admission share
- admissions/show
- Allocation Index
- allocation-change classification: demand-led, support/community-led, site-led, supply/distribution-led, or unknown

If show counts are missing, do not calculate Allocation Index.

Milo must produce the evidence-led allocation judgment before asking an operator
to interpret it:
- compare planned allocation when available against actual show counts
- compare Day 1 shows against later opening-frame shows when available
- identify protect / expand / hold / reduce / cut candidates from observed
  admissions per show, show share, admission share, and Allocation Index
- separate confident machine inference from unresolved operator rationale

Ask Dias or Akhil only for the hidden context the data cannot reveal, such as:
- deliberate PH / relationship support
- DCP, KDM, studio, or schedule constraints
- NOBAR / community / site-specific exceptions
- whether a machine-inferred allocation lesson matches programming intent

Do not ask an operator to do analysis that Grafana evidence can support.

## Step 5: Closeout Output

Use the mandatory weekly insight structure:

1. Pre-release read
- what Aigle believed before release
- 2-4 lines max

2. Outcome read
- what Day 1 and opening frame showed
- include SAMS vs Cinepoint only if it changes the operator lesson

3. Operator action
- what SAMS did: protected, expanded, cut, held, or tested
- classify the action as demand-led, support/community-led, site-led, supply/distribution-led, or unknown

4. Organic Demand Notes
- 1-3 bullets only
- focus on real-world pull beyond YouTube: intent, conversation, community hook, operator rationale, or outcome feedback

5. Lesson for next cycle
- one clear rule, question, or watch item Aigle should carry forward

## Step 6: Programming Win

Output exactly one:

- `PROGRAMMING_WIN: [concise evidence-led win]`
- `NO_PROGRAMMING_WIN_YET: [why]`

Do not force a win.

## Step 7: Sheet / Dashboard Corrections

If Sheet/dashboard rows already exist:
- do not post duplicates
- return corrections/closeout only

If fields need correction:
- list exact title, field, current value, proposed value, source, and confidence

## Step 8: Product Proof Ledger

At the end of every Monday closeout, return a section labeled exactly:

`PRODUCT_PROOF_LEDGER_UPDATE`

It must include exactly these fields, in this order:
- Week
- User
- Decision moment
- Aigle output
- Observed impact
- Verdict
- Code / workflow change
- Evidence gaps
- Write to ledger: YES / NO

Rules:
- Do not claim product proof from machine improvement alone.
- Do not claim operator decision movement unless there is evidence someone changed or defended a programming decision because of Aigle.
- If evidence is internal only, say internal proof, not operator proof.
- If the row is not honest enough to write, label `Write to ledger: NO`.

## Success Condition

Monday closeout is successful only when:
- public/private layers are labeled
- opening-frame day count is correct
- revised Day 1 logic is checked where applicable
- Day 2 allocation read is included or explicitly blocked
- each operating title has one practical lesson
- programming win is stated or explicitly absent

If any required private data is missing, the correct result is a blocker receipt, not a fake closeout.
