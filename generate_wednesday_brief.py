#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILMS_PATH = ROOT / 'films.json'
OPERATING_WEEK_PATH = ROOT / 'operating_week.json'
WEEKLY_STATE_PATH = ROOT / 'weekly_state.json'


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_films():
    data = load_json(FILMS_PATH)
    films = data.get('films', []) if isinstance(data, dict) else data
    return {film['title']: film for film in films if isinstance(film, dict) and isinstance(film.get('title'), str)}


def format_views(value):
    if value is None:
        return '—'
    if value >= 1_000_000:
        return f'{value / 1_000_000:.2f}Jt'.rstrip('0').rstrip('.')
    if value >= 1_000:
        return f'{round(value / 1_000):.0f}Rb'
    return str(value)


def describe_week(films):
    if not films:
        return 'Tidak ada film dalam operating slate.'

    leader = max(films, key=lambda film: film.get('youtube_views') or 0)
    high_count = sum(1 for film in films if film.get('buzz_level') == 'TINGGI')
    medium_count = sum(1 for film in films if film.get('buzz_level') == 'SEDANG')
    if high_count:
        return f"{leader['title']} memimpin. {high_count} film buzz tinggi, {medium_count} film buzz sedang."
    if medium_count:
        return f"{leader['title']} memimpin. Tidak ada film buzz tinggi, tapi ada {medium_count} film buzz sedang."
    return f"{leader['title']} memimpin, tapi slate tetap lemah dari sisi trailer traction."


def main():
    films_by_title = load_films()
    operating_week = load_json(OPERATING_WEEK_PATH)
    weekly_state = load_json(WEEKLY_STATE_PATH) if WEEKLY_STATE_PATH.exists() else {}

    titles = operating_week.get('films_releasing', [])
    films = [films_by_title[title] for title in titles if title in films_by_title]

    print(f"Update utk rilis {operating_week.get('week_label')} yang main di SAMS:")
    print('')
    for film in films:
        tiktok = film.get('tiktok')
        gt = film.get('google_trends')
        print(
            f"- {film['title']} — YouTube {format_views(film.get('youtube_views'))} "
            f"({film.get('buzz_level')}), TikTok {tiktok if tiktok is not None else 'pending'}, "
            f"Google Trends {gt if gt is not None else 'pending'}"
        )

    print('')
    print('Quick read:')
    print(describe_week(films))

    missing_human = weekly_state.get('missing_human_inputs', [])
    missing_auto = weekly_state.get('missing_autofillable_inputs', [])
    missing_audit = weekly_state.get('missing_audit_inputs', [])

    if missing_human or missing_auto or missing_audit:
        print('')
        print('Pending:')
        for group in missing_human + missing_auto + missing_audit:
            print(f"- {group['title']}: {', '.join(group['fields'])}")


if __name__ == '__main__':
    main()
