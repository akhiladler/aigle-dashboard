# Milo Skill: Wednesday Ops Lead Pipeline

**Goal:** By 12pm Wednesday, Aigle must have a validator-clean export, the correct SAMS slate, current pre-release signals, and a draft brief ready for Akhil.

## Milo Role
Milo is the machine-side ops lead on Wednesday.

That means Milo should:
- verify the operating slate early
- collect and normalize bounded data
- run validation before publish
- draft the operator brief
- escalate only when the work needs judgment

Milo should **not**:
- guess through source conflicts
- change product logic or schema
- invent TikTok scores
- make final strategic calls

## Canonical Files
- `pipeline_config.json` = machine rules
- `operating_week.json` = canonical weekly slate
- `films.json` = public dashboard export
- `weekly_state.json` = machine readiness state

Think of them like this:
- `films.json` = the data
- `operating_week.json` = this week's target
- `weekly_state.json` = the readiness verdict

## Wednesday Workflow
### Step 1: Generate the operating slate
Run:

```bash
python select_operating_week.py
```

Re-read `operating_week.json`. If the slate is obviously wrong, stop and escalate to Akhil.

If `operating_week.json` conflicts with `films_schedule.json` or current release-facing evidence:
- do not answer as if the slate is trustworthy
- emit `STATE_MISMATCH`
- include:
  - file path
  - `week_label`
  - `week_start`
  - `updated_at`
  - the exact conflicting titles or dates
- escalate before continuing

### Step 1.5: Repo preflight
Do not fail just because the repo has unrelated dirty files.

Only stop immediately if:
- merge / rebase / cherry-pick is in progress
- conflict markers exist in canonical publish files

Unrelated dirty task files are not a reason to abort the whole Wednesday pipeline.

### Step 2: Collect YouTube for active titles
Preferred path:

```bash
python update_youtube_signals.py --titles "Title 1" "Title 2"
```

For each title in `operating_week.json -> films_releasing`:
- prefer the direct fallback collector first
- if the fallback collector is unavailable, then do a manual trailer lookup
- update `youtube_views`
- update `youtube_url`
- recalculate `buzz_level`

Do not stop at the first failed tool.

If `yt-dlp` search is bot-gated:
- use YouTube search HTML to get candidate video IDs
- open the watch pages
- prefer PH / `CINEMA 21` / `CGV` official trailers
- reject reaction / press-conference / recap / commentary clips

### Step 3: Handle Google Trends
Use the canonical dual-track GT rule in `pipeline_config.json`.

Milo may:
- collect the GT score, or
- prefill the GT capture context if the score must be confirmed manually

If GT is present in `films.json`, Milo must also keep these audit fields current:
- `gt_benchmark_title`
- `gt_capture_context`
- `gt_entity_type`
- `gt_capture_date`
- `gt_capture_stage`

Milo must **not** invent GT scores.

### Step 4: Leave TikTok to Akhil/Dias
If `tiktok` is missing, leave it missing and let validation surface it as a human-input dependency.

### Step 5: Validate and build weekly state
Run:

```bash
python validate_films.py
python check-films.py
```

If validation fails or `check-films.py` fails, do not publish. Escalate with the exact blocker.

### Step 6: Draft the Wednesday brief
Run:

```bash
python generate_wednesday_brief.py
```

Send the draft output to Akhil. Keep it short and factual.

### Step 7: Commit and push
Only if validation passes and the machine side is ready:

```bash
python publish_dashboard_state.py --repo-root /root/aigle-dashboard --message "Milo: Wednesday pipeline [date]" --push
```

This script stages only canonical dashboard-state files and ignores unrelated dirty files.

## Publish Rules
- Publish must fail loudly on stale or inconsistent operating week state.
- Publish must fail if a title in `operating_week.json` is missing from `films.json`.
- Publish must fail if `buzz_level` contradicts `youtube_views`.
- Missing TikTok is allowed, but it must be visible in `weekly_state.json`.

## Escalate to Akhil If
- title/entity ambiguity cannot be resolved cleanly
- GT matching is inconsistent across titles
- a SAMS-relevant title is missing from the dataset
- TikTok is still pending close to deadline
- validation fails and the issue is not a simple data omission
- `operating_week.json` conflicts with `films_schedule.json` or live release evidence
