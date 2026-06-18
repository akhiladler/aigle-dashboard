#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "pipeline_config.json"
OPERATING_WEEK_PATH = ROOT / "operating_week.json"
WEEKLY_STATE_PATH = ROOT / "weekly_state.json"
OUTPUT_PATH = ROOT / "live_slate_state.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def now_jakarta(config):
    return datetime.now(ZoneInfo(config["timezone"])).isoformat(timespec="seconds")


def by_title(rows):
    result = {}
    for row in rows or []:
        title = row.get("title")
        if isinstance(title, str):
            result[title] = row
    return result


def detect_state(operating_week, weekly_state):
    operating_titles = operating_week.get("films_releasing") or []
    weekly_titles = weekly_state.get("films_in_scope") or []
    if operating_week.get("week_start") != weekly_state.get("week_start"):
        return "STATE_MISMATCH", "operating_week.week_start differs from weekly_state.week_start"
    if operating_titles != weekly_titles:
        return "STATE_MISMATCH", "operating_week.films_releasing differs from weekly_state.films_in_scope"
    sams_confirmation = operating_week.get("sams_confirmation") or {}
    if sams_confirmation.get("status") not in ("confirmed", "confirmed_from_tracked_records"):
        return "PARTIAL_OPERATOR_GRAFANA_UNVERIFIED", sams_confirmation.get("blocker")
    return "ALIGNED_DASHBOARD_ONLY", None


def main():
    config = load_json(CONFIG_PATH)
    operating_week = load_json(OPERATING_WEEK_PATH)
    weekly_state = load_json(WEEKLY_STATE_PATH)
    generated_at = now_jakarta(config)

    weekly_by_title = by_title(weekly_state.get("film_status"))
    public_candidates = operating_week.get("public_release_candidates") or []
    sams_confirmation = operating_week.get("sams_confirmation") or {}
    status, blocker = detect_state(operating_week, weekly_state)

    active_titles = []
    for title in operating_week.get("films_releasing") or []:
        active_titles.append(
            {
                "title": title,
                "dashboard_state": weekly_by_title.get(title, {}),
                "dashboard_status": "tracked_sams_candidate",
                "operator_schedule_status": "missing_receipt",
                "grafana_reality_status": "missing_receipt",
                "render_group": "sams_tracked_candidate",
            }
        )

    payload = {
        "contract": "aigle_live_slate_state.v0",
        "generated_at": generated_at,
        "week_label": operating_week.get("week_label"),
        "week_start": operating_week.get("week_start"),
        "status": status,
        "state_mismatch": status == "STATE_MISMATCH",
        "blocker": blocker,
        "layers": {
            "dashboard_state": {
                "source_files": [
                    "operating_week.json",
                    "weekly_state.json",
                    "films.json",
                    "films_schedule.json",
                ],
                "status": "loaded",
                "titles": operating_week.get("films_releasing") or [],
                "ready_for_publish": weekly_state.get("ready_for_publish"),
                "ready_for_operator": weekly_state.get("ready_for_operator"),
            },
            "operator_schedule": {
                "status": "missing_receipt",
                "titles": None,
                "receipt": None,
                "note": "No durable full SAMS booking/showtime confirmation receipt is attached.",
            },
            "grafana_reality": {
                "status": "missing_receipt",
                "titles": None,
                "receipt": None,
                "note": "No current Grafana active-title/show allocation receipt is attached.",
            },
        },
        "sams_confirmation": sams_confirmation,
        "active_titles": active_titles,
        "public_release_candidates": public_candidates,
        "render_rules": {
            "primary_titles": "active_titles",
            "candidate_titles": "public_release_candidates",
            "show_state_mismatch": "state_mismatch",
            "do_not_present_public_candidates_as_sams_confirmed": True,
        },
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(str(OUTPUT_PATH))
    print(f"LIVE_SLATE_STATUS={status}")
    if blocker:
        print(f"LIVE_SLATE_BLOCKER={blocker}")


if __name__ == "__main__":
    main()
