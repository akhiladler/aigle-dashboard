#!/usr/bin/env python3
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / 'films_schedule.json'
OUTPUT_PATH = ROOT / 'operating_week.json'

TODAY = date.fromisoformat('2026-04-06')
LOOKAHEAD_DAYS = 10


def load_schedule():
    data = json.loads(SCHEDULE_PATH.read_text())
    return data['films']


def main():
    films = load_schedule()
    window_end = TODAY + timedelta(days=LOOKAHEAD_DAYS)

    in_window = []
    for film in films:
        d = date.fromisoformat(film['date'])
        if TODAY <= d <= window_end and film.get('status') != 'postponed':
            in_window.append(film)

    grouped = {}
    for film in in_window:
        grouped.setdefault(film['date'], []).append(film)

    upcoming_dates = sorted(grouped.keys())
    primary_date = upcoming_dates[0] if upcoming_dates else None
    primary_films = grouped.get(primary_date, []) if primary_date else []

    payload = {
        'as_of': TODAY.isoformat(),
        'lookahead_days': LOOKAHEAD_DAYS,
        'upcoming_release_dates': upcoming_dates,
        'primary_operating_date': primary_date,
        'primary_operating_titles': [f['title'] for f in primary_films],
        'counts_by_date': {d: len(grouped[d]) for d in upcoming_dates},
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    print(str(OUTPUT_PATH))


if __name__ == '__main__':
    main()
