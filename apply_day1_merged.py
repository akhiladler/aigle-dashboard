#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FILMS_PATH = ROOT / "films.json"

DAY1_FIELDS = [
    "day1_national_adm",
    "day1_national_screens",
    "day1_national_adm_show",
    "day1_sams_adm",
    "day1_sams_shows",
    "day1_sams_adm_show",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply merged Day 1 values into films.json.")
    parser.add_argument("--input", type=Path, required=True, help="Path to merged Day 1 JSON.")
    parser.add_argument("--films", type=Path, default=FILMS_PATH, help="Path to films.json.")
    parser.add_argument("--write", action="store_true", help="Write changes back to films.json.")
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    films_payload = load_json(args.films)
    merged_payload = load_json(args.input)

    if isinstance(films_payload, dict):
        films = films_payload.get("films", [])
    else:
        films = films_payload

    by_key = {}
    for film in films:
        if not isinstance(film, dict):
            continue
        key = (film.get("title"), film.get("release_date"))
        by_key[key] = film

    updated = []
    missing = []

    for item in merged_payload.get("matched", []):
        title = item.get("title")
        release_date = item.get("release_date")
        target = by_key.get((title, release_date))
        if target is None:
            missing.append({"title": title, "release_date": release_date})
            continue

        changed_fields = []
        for field in DAY1_FIELDS:
            if field in item:
                old = target.get(field)
                new = item.get(field)
                if old != new:
                    target[field] = new
                    changed_fields.append(field)

        if changed_fields:
            updated.append({
                "title": title,
                "release_date": release_date,
                "fields": changed_fields,
            })

    rendered = {
        "updated": updated,
        "missing": missing,
        "write_requested": args.write,
    }

    if args.write:
        args.films.write_text(json.dumps(films_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(rendered, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
