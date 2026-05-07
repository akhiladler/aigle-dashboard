#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Merge SAMS and Cinepoint Day 1 parsed outputs.")
    parser.add_argument("--cinepoint", type=Path, required=True)
    parser.add_argument("--sams", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    args = parse_args()
    cinepoint = load_json(args.cinepoint)
    sams = load_json(args.sams)

    by_title = {}

    for item in cinepoint.get("matched", []):
        title = item.get("matched_title")
        if not title:
            continue
        by_title.setdefault(title, {"title": title, "release_date": item.get("release_date")})
        by_title[title].update(
            {
                "day1_national_adm": item.get("day1_national_adm"),
                "day1_national_screens": item.get("day1_national_screens"),
                "day1_national_adm_show": item.get("day1_national_adm_show"),
                "cinepoint_estimated_opening": item.get("estimated_opening"),
                "cinepoint_cumulative": item.get("cumulative"),
            }
        )

    for item in sams.get("matched", []):
        title = item.get("matched_title")
        if not title:
            continue
        by_title.setdefault(title, {"title": title, "release_date": item.get("release_date")})
        by_title[title].update(
            {
                "day1_sams_adm": item.get("day1_sams_adm"),
                "day1_sams_shows": item.get("day1_sams_shows"),
                "day1_sams_adm_show": item.get("day1_sams_adm_show"),
            }
        )

    merged = []
    for item in by_title.values():
        if item.get("day1_national_adm_show") is not None and item.get("day1_sams_adm_show") is not None:
            item["adm_show_gap_national_minus_sams"] = round(
                item["day1_national_adm_show"] - item["day1_sams_adm_show"], 2
            )
        merged.append(item)

    output = {
        "matched": sorted(merged, key=lambda item: (item.get("release_date") or "", item["title"])),
        "cinepoint_unmatched": cinepoint.get("unmatched", []),
        "sams_unmatched": sams.get("unmatched", []),
    }

    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
