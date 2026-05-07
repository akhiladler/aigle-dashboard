# Milo Task: Thursday Release-Day Reality Check

**Burden removed:** Akhil should not discover on Friday that Thursday's live slate drifted from Wednesday's assumptions.

## When to Run
- Thursday morning
- Thursday late afternoon if needed
- Also run if Dias or 21 suggests a title changed, slipped, or disappeared

## Goal
Confirm that the real release-day slate still matches `operating_week.json`.

## Task

### Step 1: Read the expected live slate
Read:
- `operating_week.json`
- `films_schedule.json`

Expected source of truth for this week:
- `operating_week.json -> films_releasing`

If `operating_week.json` contradicts the current `films_schedule.json` entries for the target date:
- do not continue as if the target slate is settled
- report `STATE_MISMATCH`
- include the exact file paths, `week_label`, `week_start`, `updated_at`, and conflicting titles
- escalate immediately before checking live reality

### Step 2: Check live release reality
Use current release-facing sources, in this order:
1. 21cineplex
2. direct SAMS / Dias confirmation if available
3. other operator evidence only if the first two are incomplete

Check:
- are all expected titles actually live?
- did any expected title disappear?
- did any unexpected local title appear?
- did any title shift date?

For each questioned title on 21cineplex:
- check both the list page state (`/nowplaying`, `/comingsoon`) and the title-specific page if one exists
- capture the exact URL and exact label / playing-date line used
- if the list pages and the title page disagree, do **not** force a normal mismatch verdict
- report `SOURCE_CONFLICT` with receipts and escalate before recommending a slate change
- only report `CONFIRMED_MISMATCH` if the relevant 21 evidence aligns in the same direction

### Step 3: Apply SAMS filters again
Only care about:
- local titles
- not Rapi Films
- plausibly SAMS-relevant

Do not clutter the report with excluded foreign titles unless they affect the interpretation.

### Step 4: Report only the delta
Format:

```text
Thursday release check: [date]
Expected slate: [...]
Live slate: [...]
Status: match / mismatch
Changes:
- [title] disappeared / delayed
- [title] newly appeared
- [title] date shifted
Action:
- no change needed
or
- update operating_week.json before Friday
```

### Step 5: If mismatch, escalate immediately
If live release reality differs from `operating_week.json`:
- do not wait for Friday
- flag the exact mismatch
- recommend the exact file update needed

## Rules
- no guessing
- no summary without evidence
- no pretending Wednesday assumptions are still true if Thursday reality changed
- if nothing changed, say `Status: match`
- if the target slate itself is stale or contradictory, say `STATE_MISMATCH` instead of pretending the check passed
- if 21cineplex sources conflict internally, say `SOURCE_CONFLICT` instead of pretending the check passed
