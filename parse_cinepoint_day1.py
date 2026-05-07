#!/usr/bin/env python3
import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent
FILMS_PATH = ROOT / "films.json"
SCHEDULE_PATH = ROOT / "films_schedule.json"

ADMISSIONS_HEADER_RE = re.compile(r"ESTIMATED ADMISSION\s*-\s*.+", re.IGNORECASE)
SHOWTIMES_HEADER_RE = re.compile(r"SHOWTIMES\s*-\s*.+", re.IGNORECASE)
TAGGED_LINE_RE = re.compile(r"^#(?P<tag>[A-Za-z0-9]+)\s+(?P<body>.+?)\s*$")
TAG_ONLY_RE = re.compile(r"^#(?P<tag>[A-Za-z0-9]+)\s*$")
OPENING_RE = re.compile(r"(?P<value>[\d,]+)\s+\(estimated opening\)", re.IGNORECASE)
DELTA_TOTAL_RE = re.compile(
    r"\+(?P<delta>[\d,]+)\s+\((?P<pct>[+-]?\d+(?:\.\d+)?)%\)\s+\|\s+(?P<total>[\d,]+)",
    re.IGNORECASE,
)
SHOW_RE = re.compile(r"(?P<shows>[\d,]+)\s+\((?P<pct>[+-]?\d+(?:\.\d+)?)%\)", re.IGNORECASE)
SHOW_OPENING_RE = re.compile(r"(?P<shows>[\d,]+)\s+\(opening\)", re.IGNORECASE)


@dataclass
class ParsedFilm:
    raw_tag: str
    guessed_title: str
    admissions: Optional[int] = None
    cumulative: Optional[int] = None
    estimated_opening: bool = False
    shows: Optional[int] = None
    matched_title: Optional[str] = None
    release_date: Optional[str] = None

    @property
    def adm_per_show(self) -> Optional[float]:
        if self.admissions is None or not self.shows:
            return None
        return round(self.admissions / self.shows, 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Cinepoint Thursday Day 1 text into structured film data."
    )
    parser.add_argument("--input", type=Path, help="Path to raw Cinepoint text file. Defaults to stdin.")
    parser.add_argument(
        "--release-date",
        help="Limit title matching to films scheduled on this release date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--write-films",
        action="store_true",
        help="Write matched day1 values back into films.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save the parsed JSON output.",
    )
    return parser.parse_args()


def read_text(path: Optional[Path]) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    return sys.stdin.read()


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("&", " and ")
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    value = re.sub(r"([A-Za-z])(\d)", r"\1 \2", value)
    value = re.sub(r"(\d)([A-Za-z])", r"\1 \2", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).strip().lower()
    return re.sub(r"\s+", " ", value)


def hashtag_to_title(tag: str) -> str:
    interim = re.sub(r"([a-z])([A-Z])", r"\1 \2", tag).strip()
    interim = re.sub(r"([A-Za-z])(\d)", r"\1 \2", interim)
    interim = re.sub(r"(\d)([A-Za-z])", r"\1 \2", interim)
    words = interim.split()
    if words and words[-1].isdigit() and len(words[-1]) == 4:
        words[-1] = words[-1]
    return " ".join(words)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schedule_candidates(release_date: Optional[str]) -> List[dict]:
    schedule = load_json(SCHEDULE_PATH).get("films", [])
    if release_date:
        return [film for film in schedule if film.get("date") == release_date]
    return schedule


def parse_sections(raw_text: str) -> Tuple[List[str], List[str]]:
    admission_lines: List[str] = []
    show_lines: List[str] = []
    current = None
    pending_tag: Optional[str] = None

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line == "---":
            continue
        if ADMISSIONS_HEADER_RE.search(line):
            current = "admissions"
            continue
        if SHOWTIMES_HEADER_RE.search(line):
            pending_tag = None
            current = "shows"
            continue
        if current == "admissions":
            if line.startswith("#"):
                tag_only = TAG_ONLY_RE.match(line)
                if tag_only:
                    pending_tag = tag_only.group("tag")
                    continue
                admission_lines.append(line)
                pending_tag = None
                continue
            if pending_tag:
                admission_lines.append(f"#{pending_tag} {line}")
                pending_tag = None
                continue
        elif current == "shows" and line.startswith("#"):
            show_lines.append(line)

    return admission_lines, show_lines


def parse_admission_line(line: str) -> Optional[ParsedFilm]:
    match = TAGGED_LINE_RE.match(line)
    if not match:
        return None

    tag = match.group("tag")
    body = match.group("body")
    film = ParsedFilm(raw_tag=tag, guessed_title=hashtag_to_title(tag))

    opening = OPENING_RE.search(body)
    if opening:
        film.admissions = parse_int(opening.group("value"))
        film.estimated_opening = True
        return film

    delta_total = DELTA_TOTAL_RE.search(body)
    if delta_total:
        film.admissions = parse_int(delta_total.group("delta"))
        film.cumulative = parse_int(delta_total.group("total"))
        return film

    return film


def parse_show_line(line: str) -> Optional[Tuple[str, int]]:
    match = TAGGED_LINE_RE.match(line)
    if not match:
        return None

    tag = match.group("tag")
    body = match.group("body")

    opening = SHOW_OPENING_RE.search(body)
    if opening:
        return tag, parse_int(opening.group("shows"))

    standard = SHOW_RE.search(body)
    if standard:
        return tag, parse_int(standard.group("shows"))

    return None


def parse_int(value: str) -> int:
    return int(value.replace(",", ""))


def score_match(raw_title: str, candidate_title: str) -> Tuple[int, int]:
    raw_norm = normalize_text(raw_title)
    candidate_norm = normalize_text(candidate_title)
    raw_compact = raw_norm.replace(" ", "")
    candidate_compact = candidate_norm.replace(" ", "")

    if raw_norm == candidate_norm:
        return (0, 0)
    if raw_compact == candidate_compact:
        return (0, 1)
    if raw_norm in candidate_norm or candidate_norm in raw_norm:
        return (1, abs(len(candidate_norm) - len(raw_norm)))
    if raw_compact in candidate_compact or candidate_compact in raw_compact:
        return (1, abs(len(candidate_compact) - len(raw_compact)))

    raw_words = set(raw_norm.split())
    candidate_words = set(candidate_norm.split())
    overlap = len(raw_words & candidate_words)
    union = len(raw_words | candidate_words) or 1
    return (2, -int((overlap / union) * 100))


def match_titles(parsed: Dict[str, ParsedFilm], candidates: List[dict]) -> List[dict]:
    unmatched = []
    candidate_titles = [film["title"] for film in candidates if film.get("title")]

    for item in parsed.values():
        scored = sorted(
            ((score_match(item.guessed_title, title), title) for title in candidate_titles),
            key=lambda pair: pair[0],
        )
        if not scored:
            unmatched.append({"raw_tag": item.raw_tag, "guessed_title": item.guessed_title, "reason": "no candidates"})
            continue

        best_score, best_title = scored[0]
        best_rank = best_score[0]
        if best_rank > 1:
            unmatched.append(
                {
                    "raw_tag": item.raw_tag,
                    "guessed_title": item.guessed_title,
                    "reason": "low-confidence title match",
                    "best_candidate": best_title,
                }
            )
            continue

        item.matched_title = best_title
        item.release_date = next((film["date"] for film in candidates if film.get("title") == best_title), None)

    return unmatched


def build_output(parsed: Dict[str, ParsedFilm], unmatched: List[dict]) -> dict:
    films = []
    for item in parsed.values():
        films.append(
            {
                "raw_tag": item.raw_tag,
                "guessed_title": item.guessed_title,
                "matched_title": item.matched_title,
                "release_date": item.release_date,
                "day1_national_adm": item.admissions,
                "day1_national_screens": item.shows,
                "day1_national_adm_show": item.adm_per_show,
                "cumulative": item.cumulative,
                "estimated_opening": item.estimated_opening,
            }
        )

    unmatched_tags = {item["raw_tag"] for item in unmatched if "raw_tag" in item}
    unmatched_films = [film for film in films if not film["matched_title"] and film["raw_tag"] not in unmatched_tags]
    return {"matched": [film for film in films if film["matched_title"]], "unmatched": unmatched + unmatched_films}


def write_films_json(parsed: Dict[str, ParsedFilm]) -> int:
    payload = load_json(FILMS_PATH)
    films = payload.get("films", [])
    updated = 0
    for film in films:
        title = film.get("title")
        match = next((item for item in parsed.values() if item.matched_title == title), None)
        if not match:
            continue
        film["day1_national_adm"] = match.admissions
        film["day1_national_screens"] = match.shows
        film["day1_national_adm_show"] = match.adm_per_show
        updated += 1

    FILMS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=6), encoding="utf-8")
    return updated


def main() -> int:
    args = parse_args()
    raw_text = read_text(args.input)
    admission_lines, show_lines = parse_sections(raw_text)

    parsed: Dict[str, ParsedFilm] = {}
    for line in admission_lines:
        film = parse_admission_line(line)
        if film:
            parsed[film.raw_tag] = film

    for line in show_lines:
        parsed_show = parse_show_line(line)
        if not parsed_show:
            continue
        tag, shows = parsed_show
        if tag not in parsed:
            parsed[tag] = ParsedFilm(raw_tag=tag, guessed_title=hashtag_to_title(tag))
        parsed[tag].shows = shows

    candidates = load_schedule_candidates(args.release_date)
    unmatched = match_titles(parsed, candidates)
    output = build_output(parsed, unmatched)

    if args.write_films:
        output["films_json_updated"] = write_films_json(parsed)

    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
