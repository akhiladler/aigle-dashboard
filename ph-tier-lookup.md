# PH Tier Lookup — Canonical Source

**Purpose:** Exact-match lookup table for auto-filling `ph_tier` in films.json.
**Rule:** Match on `PH Name` exactly (case-insensitive). No fuzzy matching. No guessing.
If no match → `ph_tier: null` + `needs_ph_review: true`.

**Format:** `PH Name | Tier | Notes`

---

## Tier 1 — Giants (XXI cartel, guaranteed screens)

MD Pictures | T1 | Manoj Punjabi. Listed on JSX.
Falcon Pictures | T1 | HB Naveen, Frederica.
Falcon | T1 | Alias for Falcon Pictures.
Legacy Pictures | T1 | Robert Ronny. #1 by releases.
Starvision | T1 | Chand Parwez Servia.
Starvision Plus | T1 | Alias for Starvision.

## Tier 2 — Established

RAPI Films | T2 | Does NOT play at SAMS.
Rapi Films | T2 | Alias.
Visinema Pictures | T2 | SAMS-Visinema multiplier confirmed.
MVP Pictures | T2 | Raam Punjabi. Owns Platinum Cineplex.
MNC Pictures | T2 | MNC Media Group.
Miles Films | T2 | Mira Lesmana, Riri Riza.
Screenplay Films | T2 | Wicky V. Olindo.
BASE Entertainment | T2 |
Sinemart | T2 |
Soraya Intercine | T2 |

## Tier 3 — Rising

Imajinari | T3 | Ernest Prakasa. Agak Laen.
Pichouse Films | T3 |
786 Productions | T3 |
IDN Media | T3 |
Screenplay Bumilangit | T3 | Gundala.
SinemaArt | T3 |
Heart Pictures | T3 | Herty Purba.
Paragon Pictures | T3 |
Sinemaku Pictures | T3 |
Lyto Pictures | T3 |
Tiger Wong Entertainment | T3 |

## Tier 4 — Micro/Indie

Citra Sinema Kreasi | T4 |
Entelekey Media Indonesia | T4 |
MVP Pictures (indie arm) | T4 |
Shen Entertainment | T4 |
Puras Production | T4 |
PIM Pictures | T4 |
Ruang Rangkai Kata | T4 |
Trois Global Film | T4 |
Eight Senses Film | T4 |
Pabrik Imaji Akasacara | T4 |
Radepa Konten Indonesia | T4 |
Alamanda Mandiri Sejahtera | T4 |
DHF Entertainment | T4 |
Aksa Bumi Langit | T4 |
Impian Indonesia | T4 |
Tunas Citrasinema Kreatif | T4 |
Sinema Digital Indonesia | T4 |
Kasih Karunia Film | T4 |
Lex Pictures | T4 |
Ess Jay Studios | T4 |
Sinemata Indonesia Pratama | T4 |
VMS | T4 |
Summerland | T4 | Co-producer Yohanna (Apr 2026). Source: ANTARA, Kompas.
Reason8 Films | T4 | Co-producer Yohanna (Apr 2026). Source: KapanLagi.
Pilgrim Film | T4 | Co-producer Yohanna (Apr 2026). Source: 21cineplex.

---

## Maintenance

- When a new PH appears in films.json, add it here with a tier.
- If unsure → leave out, let Milo flag `needs_ph_review: true`.
- Richer context (history, ownership, notes) lives in `production-houses.md`. This file is lookup only.

*Created: Apr 8, 2026*
