# Milo Task: Monday OW Data Collection

**Burden removed:** Akhil no longer has to manually check Cinepoint for Opening Weekend numbers on Monday.

## When to Run
Every Monday morning.

## Task

### Step 1: Check Cinepoint
Go to Cinepoint (or the source Akhil specifies) and look for Opening Weekend data for films that released the previous week.

The films to check are in `operating_week.json` → `films_releasing`.

### Step 2: Collect data
For each film, record:
- `ow_national`: Opening Weekend national admissions (cumulative through Sunday)
- Source URL or screenshot

### Step 3: Update films.json
For each film, update ONLY:
- `ow_national`

Do NOT touch any other field. Do NOT touch other films.

### Step 4: Report to Akhil (Telegram)
Max 100 words. Format:

```
Monday OW: [date]
[Film 1]: OW [number] ([multiplier]x vs Day 1)
[Film 2]: OW [number] ([multiplier]x vs Day 1)
Source: Cinepoint [date]
```

### Step 5: Commit + push
Commit: "Milo: OW data [date]"

## Important
- Cinepoint revises OW numbers ±35%. ALWAYS use the Monday post, not earlier estimates.
- If Cinepoint hasn't posted yet, WAIT. Do not use media articles. Report "Cinepoint not yet posted" and retry later.
- If OW data is not available for a film, report it. Do not guess.
