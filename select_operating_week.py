#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / 'pipeline_config.json'
FILMS_PATH = ROOT / 'films.json'
SCHEDULE_PATH = ROOT / 'films_schedule.json'
OUTPUT_PATH = ROOT / 'operating_week.json'


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_config():
    return load_json(CONFIG_PATH)


def load_films():
    data = load_json(FILMS_PATH)
    return data.get('films', []) if isinstance(data, dict) else data


def load_schedule():
    data = load_json(SCHEDULE_PATH)
    return data.get('films', []) if isinstance(data, dict) else []


def current_local_date(timezone_name):
    return datetime.now(ZoneInfo(timezone_name)).date()


def parse_args(config):
    parser = argparse.ArgumentParser(description='Generate canonical operating_week.json for Aigle.')
    parser.add_argument('--today', help='Override local date in YYYY-MM-DD format.')
    parser.add_argument('--updated-by', default=config.get('ops_lead', 'milo'))
    return parser.parse_args()


def resolve_today(args, config):
    if args.today:
        return date.fromisoformat(args.today)
    return current_local_date(config['timezone'])


def format_week_label(d):
    month_map = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec',
    }
    return f"{d.day} {month_map[d.month]}"


def group_schedule(schedule):
    grouped = defaultdict(list)
    for film in schedule:
        if not isinstance(film, dict) or film.get('status') == 'postponed':
            continue
        try:
            film_date = date.fromisoformat(film['date'])
        except Exception:
            continue
        grouped[film_date].append(film)
    return grouped


def group_tracked_films(films):
    grouped = defaultdict(list)
    for film in films:
        if not isinstance(film, dict):
            continue
        if film.get('plays_at_sams') is not True:
            continue
        try:
            film_date = date.fromisoformat(film['release_date'])
        except Exception:
            continue
        grouped[film_date].append(film)
    return grouped


def choose_operating_date(today, available_dates, config):
    retention_days = config['operating_week']['active_retention_days']
    lookahead_days = config['operating_week']['lookahead_days']

    current_dates = sorted(
        d for d in available_dates
        if 0 <= (today - d).days <= retention_days
    )
    if current_dates:
        return current_dates[-1]

    upcoming_dates = sorted(
        d for d in available_dates
        if 0 <= (d - today).days <= lookahead_days
    )
    if upcoming_dates:
        return upcoming_dates[0]

    return None


def titles_for_date(primary_date, schedule_by_date, tracked_by_date):
    if primary_date is None:
        return []

    schedule_titles = [film['title'] for film in schedule_by_date.get(primary_date, []) if isinstance(film.get('title'), str)]
    tracked_films = [
        film for film in tracked_by_date.get(primary_date, [])
        if isinstance(film.get('title'), str)
    ]
    tracked_titles = [
        film['title'] for film in sorted(
            tracked_films,
            key=lambda film: film.get('youtube_views') or 0,
            reverse=True,
        )
    ]

    if tracked_titles:
        return tracked_titles

    return schedule_titles


def main():
    config = load_config()
    args = parse_args(config)
    today = resolve_today(args, config)
    timezone = ZoneInfo(config['timezone'])

    films = load_films()
    schedule = load_schedule()
    schedule_by_date = group_schedule(schedule)
    tracked_by_date = group_tracked_films(films)

    available_dates = set(schedule_by_date.keys()) | set(tracked_by_date.keys())
    primary_date = choose_operating_date(today, available_dates, config)
    primary_titles = titles_for_date(primary_date, schedule_by_date, tracked_by_date)

    payload = {
        'week_label': format_week_label(primary_date) if primary_date else None,
        'week_start': primary_date.isoformat() if primary_date else None,
        'films_releasing': primary_titles,
        'updated_at': datetime.now(timezone).isoformat(timespec='seconds'),
        'updated_by': args.updated_by,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(str(OUTPUT_PATH))
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main()
