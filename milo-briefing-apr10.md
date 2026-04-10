# Milo Briefing — April 10, 2026

Read this. It contains context from today's work session that you need.

## Key Finding: TikTok > YouTube

Scored the Apr 9 pre-commitment. Results:
- Ayah, Ini Arahnya Kemana, Ya? (YT 64K, TT 7/10): Day 1 = 82,500
- Warung Pocong (YT 129K, TT 3/10): Day 1 = 14,312
- Yohanna (YT 48K, TT 1/10): Day 1 = 1,684

YouTube predicted WP > Ayah. Reality was Ayah 6x better. TikTok was the differentiator.

This has been encoded into the dashboard as the TT_SLEEPER signal: TikTok >= 7 with YouTube below SEDANG flags a film as a potential sleeper hit.

## Compounding Requirement (NON-NEGOTIABLE)

Aigle MUST get smarter over time. Every pre-commitment scoring must produce a code change — new signal, updated weight, new flag. Never just "note" a learning. Encode it.

The pattern: observe outcome → identify surprise → write signal rule → commit to codebase.

## Crocodile Tears Status

- Release: May 7, 2026 (27 days from today)
- YouTube: 3,000 views (CGV trailer, 4 days old)
- Talamedia festival trailer: 27,000 views (1 year old) — NOT used as primary
- TikTok/GT/NOBAR: not yet measured
- Director: Tumpal Tampubolon. 30+ festivals (TIFF, Busan, BFI London). Anthony Chen producing.
- Akhil sent Tumpal the dashboard today. First filmmaker to see it.
- DO NOT mention yourself (Milo) to Tumpal or in any CT-related output.

Your CT tracker task runs every Wednesday: Apr 16, 23, 30, May 7.

## Genre Corrections Made Today

14 genre corrections in films.json after cross-checking with master sheet + IMDB:
- Senin Harga Naik: was Drama, now Drama Komedi
- Pelangi Di Mars: was Drama, now Sci-fi
- Warung Pocong: was Horor, now Horor Komedi
- Lift: was Horor, now Thriller
- Na Willa: nobar was false, now true
- Multiple subgenre additions for Drama films

Do NOT revert these. They are correct.

## Wednesday Pipeline Skill

New skill: milo-skill-wednesday-pipeline.md. This is your end-to-end Wednesday workflow. Read it. Follow it exactly. This is how we get to 20% automation.

## What's Coming

- Apr 15-19: Akhil in Bali (sister's wedding). You run Wednesday Apr 16 SOLO.
- Apr 16 is your first real test. If the pipeline works, we're at 20%.
- If it fails, report clearly. Do not hide failures.

## Your Priority Order

1. Wednesday pipeline (the ONE thing that matters)
2. CT weekly tracker (subset of pipeline)
3. Day 1 scorer (when data arrives from Cinepoint)
4. Everything else is noise until these 3 work reliably
