# Milo Skill: Wednesday Pipeline

**Burden removed:** Akhil no longer has to run the Wednesday workflow manually. One command from anywhere (including Bali) triggers the full cycle.

## What This Does
End-to-end Wednesday update: pull YouTube views → recalculate buzz → update films.json → push to dashboard → send Telegram summary.

## When to Run
Every Wednesday. Can also be triggered manually.

## Step-by-Step

### Step 1: Read operating_week.json
Read `/root/aigle-dashboard/operating_week.json` to know which week we're in and which films are releasing.

If the file is stale (>7 days old) or the week has passed, check 21cineplex.com for this week's Indonesian film releases and update operating_week.json FIRST.

### Step 2: Update YouTube views for THIS WEEK's films
For each film in the current operating week's `films_releasing` array:
1. Search YouTube for "[film title] trailer resmi 2026" or "[film title] official trailer 2026"
2. Find the most relevant trailer (prefer official channels: 21cineplex, CGV, production house)
3. Record the current view count
4. Record the YouTube URL

**ALSO** update Crocodile Tears (see milo-task-crocodile-tears-tracker.md for details).

### Step 3: Update films.json
For each film updated in Step 2:
1. Update `youtube_views` with the new count
2. Recalculate `buzz_level`:
   - TINGGI: >= 500,000
   - SEDANG: 100,000 - 499,999
   - RENDAH: < 100,000
3. Update `youtube_url` if it was missing or wrong
4. Do NOT touch any other field
5. Do NOT touch films that are NOT in this week's release list (except CT)

Update `meta.last_updated` to today's date.

### Step 4: Validate
Re-read films.json after editing. For each film you updated, print:
- Title
- Old views → New views
- Buzz level
- YouTube URL

If anything looks wrong, FIX IT before proceeding.

### Step 5: Commit and push
```
cd /root/aigle-dashboard
git add films.json operating_week.json
git commit -m "Milo: Wednesday pipeline [date] — [N] films updated"
git push
```

### Step 6: Send Telegram summary to Akhil
Max 150 words. Format:

```
Wednesday Pipeline [date]

This week: [film1], [film2], [film3]

[film1]: [old] → [new] views ([buzz level])
[film2]: [old] → [new] views ([buzz level])
[film3]: [old] → [new] views ([buzz level])

CT: [old] → [new] views ([days to release])

Dashboard updated. [link]
```

## What NOT to Do
- Do NOT update Day 1 or OW data (that's a separate task)
- Do NOT generate insights, briefs, or recommendations
- Do NOT touch TikTok, Google Trends, or NOBAR fields (those come from Dias/Akhil)
- Do NOT modify index.html
- Do NOT run on any day other than Wednesday unless Akhil explicitly asks
- Do NOT expand scope. This skill does ONE thing: update YouTube views and push.
- Do NOT add films to films.json. Only update existing entries.
- If a film is not yet in films.json, report it to Akhil. Do not add it yourself.

## Failure Handling
- If YouTube search returns no results for a film: report it in Telegram. Do NOT guess or use 0.
- If git push fails: report it. Do NOT retry silently.
- If films.json has merge conflicts: STOP. Report to Akhil.

## Verification (for Akhil)
After the pipeline runs, check:
1. https://akhiladler.github.io/aigle-dashboard/ — Ctrl+Shift+R
2. Telegram message received with correct numbers
3. Git log shows the commit
