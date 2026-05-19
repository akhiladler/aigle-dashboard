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

If SAMS opening-frame data is missing, emit:

`BLOCKED_PRIVATE_SAMS_OPENING_FRAME_MISSING`

Then still report what public data is available, but do not call the week closed.

## Step 2: Opening-Frame Label

Label the frame by release-day day count:
- Thursday release = normal Thu-Sun 4-day OW
- Wednesday release = Wed-Sun 5-day opening frame
- If D1-D4 can be derived, present it separately from Sunday cumulative

Never compare a Wednesday-to-Sunday 5-day frame blindly with a normal Thursday-to-Sunday 4-day OW.

## Step 3: Cinepoint Revision Check

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

## Success Condition

Monday closeout is successful only when:
- public/private layers are labeled
- opening-frame day count is correct
- revised Day 1 logic is checked where applicable
- Day 2 allocation read is included or explicitly blocked
- each operating title has one practical lesson
- programming win is stated or explicitly absent

If any required private data is missing, the correct result is a blocker receipt, not a fake closeout.
