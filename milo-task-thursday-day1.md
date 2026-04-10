# Milo Task: Thursday Day 1 Data Collection

**Burden removed:** Akhil no longer has to manually check Cinepoint for Day 1 numbers on Thursday/Friday.

## When to Run
Thursday or Friday (depending on when Cinepoint posts Day 1 data for the week's releases).

## Task

### Step 1: Check which films released this week
Read `operating_week.json` → `films_releasing`.

### Step 2: Collect Day 1 data from Cinepoint
For each film, record:
- `day1_national_adm`: Day 1 national admissions
- `day1_national_screens`: Day 1 national screens
- `day1_national_adm_show`: admissions / screens (calculate this)
- Source URL or screenshot

### Step 3: Update films.json
For each film, update ONLY the Day 1 fields listed above. Add `day1_source` with date and source.

Do NOT touch any other field. Do NOT touch other films.

### Step 4: Report to Akhil (Telegram)
Max 100 words. Format:

```
Day 1: [date]
[Film 1]: [adm] adm / [screens] screens = [ratio] adm/show
[Film 2]: [adm] adm / [screens] screens = [ratio] adm/show
Source: Cinepoint [date]
```

### Step 5: Commit + push
Commit: "Milo: Day 1 data [date]"

## Important
- Use Cinepoint ONLY. Never media articles for raw admission numbers.
- If Cinepoint hasn't posted yet, report "not yet available" and retry Friday.
- If a film has no Cinepoint data (too small to track), note it. Do not guess.
- Day 1 = first day of theatrical release (usually Wednesday or Thursday).
