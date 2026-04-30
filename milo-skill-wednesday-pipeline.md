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

## Wednesday Workflow
### Step 1: Generate the operating slate
Run:

```bash
python select_operating_week.py
```

Re-read `operating_week.json`. If the slate is obviously wrong, stop and escalate to Akhil.

### Step 2: Collect YouTube for active titles
For each title in `operating_week.json -> films_releasing`:
- find the best official trailer source
- update `youtube_views`
- update `youtube_url`
- recalculate `buzz_level`

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
git add films.json operating_week.json weekly_state.json
git commit -m "Milo: Wednesday pipeline [date]"
git push
```

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
