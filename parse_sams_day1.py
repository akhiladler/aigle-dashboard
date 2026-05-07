#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / "films_schedule.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse SAMS Day 1 data from CSV or plain text into structured film data."
    )
    parser.add_argument("--input", type=Path, help="Path to SAMS raw file. Defaults to stdin.")
    parser.add_argument("--release-date", help="Optional release date filter (YYYY-MM-DD).")
    parser.add_argument(
        "--format",
        choices=["auto", "csv", "text"],
        default="auto",
        help="Input format. Text format expects: Title | admissions | shows",
    )
    parser.add_argument("--output", type=Path, help="Optional output JSON path.")
    return parser.parse_args()


def read_text(path: Optional[Path]) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    return sys.stdin.read()


def load_schedule_candidates(release_date: Optional[str]) -> List[dict]:
    payload = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    films = payload.get("films", [])
    if release_date:
        return [film for film in films if film.get("date") == release_date]
    return films


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).strip().lower()
    return re.sub(r"\s+", " ", value)


def score_match(raw_title: str, candidate_title: str):
    raw_norm = normalize_text(raw_title)
    candidate_norm = normalize_text(candidate_title)
    raw_compact = raw_norm.replace(" ", "")
    candidate_compact = candidate_norm.replace(" ", "")
    if raw_norm == candidate_norm or raw_compact == candidate_compact:
        return (0, 0)
    if raw_norm in candidate_norm or candidate_norm in raw_norm:
        return (1, abs(len(candidate_norm) - len(raw_norm)))
    if raw_compact in candidate_compact or candidate_compact in raw_compact:
        return (1, abs(len(candidate_compact) - len(raw_compact)))
    raw_words = set(raw_norm.split())
    candidate_words = set(candidate_norm.split())
    overlap = len(raw_words & candidate_words)
    union = len(raw_words | candidate_words) or 1
    return (2, -int((overlap / union) * 100))


def parse_int(value: str) -> int:
    return int(str(value).replace(",", "").strip())


def parse_csv_rows(raw_text: str) -> List[Dict]:
    reader = csv.DictReader(raw_text.splitlines())
    rows = []
    for row in reader:
        title = row.get("title") or row.get("film") or row.get("Film") or row.get("Title")
        admissions = row.get("admissions") or row.get("adm") or row.get("day1_sams_adm")
        shows = row.get("shows") or row.get("showtimes") or row.get("day1_sams_shows")
        if not title:
            continue
        rows.append({"raw_title": title.strip(), "admissions": parse_int(admissions), "shows": parse_int(shows)})
    return rows


def parse_text_rows(raw_text: str) -> List[Dict]:
    rows = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            continue
        rows.append({"raw_title": parts[0], "admissions": parse_int(parts[1]), "shows": parse_int(parts[2])})
    return rows


def detect_rows(raw_text: str, fmt: str) -> List[Dict]:
    if fmt == "csv":
        return parse_csv_rows(raw_text)
    if fmt == "text":
        return parse_text_rows(raw_text)
    if "title," in raw_text.lower() or "film," in raw_text.lower():
        return parse_csv_rows(raw_text)
    return parse_text_rows(raw_text)


def match_rows(rows: List[Dict], candidates: List[dict]) -> Dict:
    candidate_titles = [film.get("title") for film in candidates if film.get("title")]
    matched = []
    unmatched = []
    for row in rows:
        if not candidate_titles:
            unmatched.append({**row, "reason": "no schedule candidates"})
            continue
        scored = sorted(((score_match(row["raw_title"], title), title) for title in candidate_titles), key=lambda pair: pair[0])
        best_score, best_title = scored[0]
        if best_score[0] > 1:
            unmatched.append({**row, "reason": "low-confidence title match", "best_candidate": best_title})
            continue
        release_date = next((film["date"] for film in candidates if film.get("title") == best_title), None)
        matched.append(
            {
                "raw_title": row["raw_title"],
                "matched_title": best_title,
                "release_date": release_date,
                "day1_sams_adm": row["admissions"],
                "day1_sams_shows": row["shows"],
                "day1_sams_adm_show": round(row["admissions"] / row["shows"], 2) if row["shows"] else None,
            }
        )
    return {"matched": matched, "unmatched": unmatched}


def main() -> int:
    args = parse_args()
    raw_text = read_text(args.input)
    rows = detect_rows(raw_text, args.format)
    candidates = load_schedule_candidates(args.release_date)
    output = match_rows(rows, candidates)
    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
