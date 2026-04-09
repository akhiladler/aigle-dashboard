#!/usr/bin/env python3
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

ROOT = Path(__file__).resolve().parent
FILMS_PATH = ROOT / 'films.json'
SCHEDULE_PATH = ROOT / 'films_schedule.json'
WEEKLY_STATE_PATH = ROOT / 'weekly_state.json'

PH_TIERS = {'T1', 'T2', 'T3', 'T4'}
BUZZ_LEVELS = {'TINGGI', 'SEDANG', 'RENDAH'}
CALENDAR_VALUES = {'PANAS', 'NORMAL', 'DINGIN'}
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

REQUIRED_STRING_FIELDS = ['title', 'release_date', 'week_label', 'ph', 'ph_tier', 'genre', 'buzz_level', 'calendar']
REQUIRED_PRESENCE_FIELDS = ['youtube_views']
NUMERIC_FIELDS = [
    'youtube_views', 'tiktok', 'google_trends', 'sams_shows',
    'day1_sams_adm', 'day1_sams_shows', 'day1_sams_adm_show',
    'day1_national_adm', 'day1_national_screens', 'day1_national_adm_show',
    'ow_sams', 'ow_national'
]
MANUAL_FIELDS = {'tiktok', 'nobar'}
AUTOFILLABLE_FIELDS = {'google_trends', 'youtube_views', 'youtube_url'}

issues = []


def add(severity, message, film=None, field=None):
    issues.append({
        'severity': severity,
        'message': message,
        'film': film,
        'field': field,
    })


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def valid_url(value):
    try:
        p = urlparse(value)
        return p.scheme in ('http', 'https') and bool(p.netloc)
    except Exception:
        return False


def rounded_ratio_ok(raw_num, raw_den, stored, tolerance=0.15):
    if raw_num is None or raw_den in (None, 0) or stored is None:
        return True
    calc = round(raw_num / raw_den, 1)
    return abs(calc - stored) <= tolerance


def load_json(path):
    return json.loads(path.read_text())


def load_data():
    try:
        data = load_json(FILMS_PATH)
    except Exception as e:
        add('ERROR', f'Failed to read/parse films.json: {e}')
        return None, None

    films = None
    meta = None
    if isinstance(data, list):
        films = data
    elif isinstance(data, dict):
        meta = data.get('meta')
        films = data.get('films')
    else:
        add('ERROR', 'Top-level JSON must be an array or object with a films array')
        return None, None

    if not isinstance(films, list):
        add('ERROR', 'films must be an array')
        return None, meta
    if not films:
        add('ERROR', 'films array is empty')
    return films, meta


def load_schedule_map():
    try:
        data = load_json(SCHEDULE_PATH)
    except Exception as e:
        add('WARN', f'Failed to read/parse films_schedule.json: {e}', field='films_schedule.json')
        return {}

    films = data.get('films') if isinstance(data, dict) else None
    if not isinstance(films, list):
        add('WARN', 'films_schedule.json does not contain a valid films array', field='films_schedule.json')
        return {}

    schedule = {}
    for item in films:
        if not isinstance(item, dict):
            continue
        title = item.get('title')
        date = item.get('date')
        if isinstance(title, str) and isinstance(date, str):
            schedule[title] = date
    return schedule


def validate_top_level(films, meta):
    if isinstance(meta, dict) and 'total_films' in meta:
        if meta['total_films'] != len(films):
            add('ERROR', f"meta.total_films={meta['total_films']} does not match films.length={len(films)}", field='meta.total_films')


def validate_film(film, idx, schedule_map):
    if not isinstance(film, dict):
        add('ERROR', f'Film at index {idx} is not an object')
        return

    title = film.get('title', f'<index {idx}>')

    for field in REQUIRED_STRING_FIELDS:
        if field not in film:
            add('ERROR', f'Missing required field: {field}', film=title, field=field)
            continue
        value = film.get(field)
        if not isinstance(value, str) or not value.strip():
            add('ERROR', f'Required field must be a non-empty string: {field}', film=title, field=field)

    for field in REQUIRED_PRESENCE_FIELDS:
        if field not in film:
            add('ERROR', f'Missing required field: {field}', film=title, field=field)

    release_date = film.get('release_date')
    if isinstance(release_date, str):
        if not DATE_RE.match(release_date):
            add('ERROR', 'release_date must match YYYY-MM-DD', film=title, field='release_date')
        else:
            try:
                datetime.strptime(release_date, '%Y-%m-%d')
            except ValueError:
                add('ERROR', 'release_date is not a valid calendar date', film=title, field='release_date')

    if film.get('ph_tier') not in PH_TIERS:
        add('ERROR', f"Invalid ph_tier: {film.get('ph_tier')}", film=title, field='ph_tier')

    if film.get('buzz_level') not in BUZZ_LEVELS:
        add('ERROR', f"Invalid buzz_level: {film.get('buzz_level')}", film=title, field='buzz_level')

    if film.get('calendar') not in CALENDAR_VALUES:
        add('ERROR', f"Invalid calendar: {film.get('calendar')}", film=title, field='calendar')

    youtube_url = film.get('youtube_url')
    if youtube_url is not None:
        if not isinstance(youtube_url, str) or not valid_url(youtube_url):
            add('ERROR', 'youtube_url must be a valid http/https URL', film=title, field='youtube_url')

    for field in NUMERIC_FIELDS:
        value = film.get(field)
        if value is None:
            continue
        if not is_number(value):
            add('ERROR', f'{field} must be numeric', film=title, field=field)
            continue
        if value < 0:
            add('ERROR', f'{field} must be non-negative', film=title, field=field)

    tiktok = film.get('tiktok')
    if tiktok is not None and is_number(tiktok) and not (0 <= tiktok <= 10):
        add('ERROR', 'tiktok must be between 0 and 10', film=title, field='tiktok')

    gt = film.get('google_trends')
    if gt is not None and is_number(gt) and not (0 <= gt <= 100):
        add('ERROR', 'google_trends must be between 0 and 100', film=title, field='google_trends')

    nobar = film.get('nobar')
    if nobar is not None and not isinstance(nobar, bool):
        add('ERROR', 'nobar must be true, false, or null', film=title, field='nobar')

    views = film.get('youtube_views')
    buzz = film.get('buzz_level')
    if is_number(views) and buzz in BUZZ_LEVELS:
        expected = 'TINGGI' if views >= 500000 else 'SEDANG' if views >= 100000 else 'RENDAH'
        if buzz != expected:
            add('ERROR', f'buzz_level={buzz} contradicts youtube_views={views} (expected {expected})', film=title, field='buzz_level')
        if views > 0 and not youtube_url:
            add('WARN', 'youtube_url missing despite positive youtube_views', film=title, field='youtube_url')

    if not rounded_ratio_ok(film.get('day1_national_adm'), film.get('day1_national_screens'), film.get('day1_national_adm_show')):
        calc = round(film['day1_national_adm'] / film['day1_national_screens'], 1)
        add('ERROR', f"day1_national_adm_show={film.get('day1_national_adm_show')} contradicts computed value {calc}", film=title, field='day1_national_adm_show')

    if not rounded_ratio_ok(film.get('day1_sams_adm'), film.get('day1_sams_shows'), film.get('day1_sams_adm_show')):
        calc = round(film['day1_sams_adm'] / film['day1_sams_shows'], 1)
        add('ERROR', f"day1_sams_adm_show={film.get('day1_sams_adm_show')} contradicts computed value {calc}", film=title, field='day1_sams_adm_show')

    scheduled_date = schedule_map.get(title)
    if scheduled_date is None:
        add('WARN', 'Title not found in films_schedule.json', film=title, field='title')
    elif release_date != scheduled_date:
        add('ERROR', f'release_date={release_date} does not match films_schedule.json date={scheduled_date}', film=title, field='release_date')


def validate_duplicates(films):
    pairs = Counter()
    titles = Counter()
    for film in films:
        if not isinstance(film, dict):
            continue
        title = film.get('title')
        release_date = film.get('release_date')
        pairs[(title, release_date)] += 1
        titles[title] += 1

    for (title, release_date), count in pairs.items():
        if title is not None and release_date is not None and count > 1:
            add('ERROR', f'Duplicate film record for ({title}, {release_date})')

    for title, count in titles.items():
        if title is not None and count > 1:
            add('WARN', f'Duplicate title appears {count} times across release dates', film=title, field='title')


def attention_score(film):
    score = 0
    views = film.get('youtube_views') or 0
    if views >= 500000:
        score += 3
    elif views >= 100000:
        score += 2
    elif views > 0:
        score += 1

    if film.get('tiktok') is None:
        score += 2
    if film.get('nobar') is None:
        score += 2
    if film.get('google_trends') is None:
        score += 1
    return score


def classify_missing(fields):
    human = [f for f in fields if f in MANUAL_FIELDS]
    autofillable = [f for f in fields if f in AUTOFILLABLE_FIELDS]
    other = [f for f in fields if f not in MANUAL_FIELDS and f not in AUTOFILLABLE_FIELDS]
    return human, autofillable, other


def build_operator_summary(this_week, ready_titles, missing_manual, anomalies):
    if not this_week:
        return 'No films in scope.'

    top = this_week[0]
    top_views = top.get('youtube_views') or 0
    if len(ready_titles) == len(this_week):
        return f"All {len(this_week)} films are ready. Top attention title: {top.get('title')} ({top_views} views)."

    missing_titles = [item['title'] for item in missing_manual]
    return (
        f"{len(ready_titles)}/{len(this_week)} films ready. "
        f"Top attention title: {top.get('title')} ({top_views} views). "
        f"Human inputs needed for: {', '.join(missing_titles)}."
    )


def build_weekly_state(films):
    films_sorted = sorted(
        [f for f in films if isinstance(f, dict) and isinstance(f.get('release_date'), str)],
        key=lambda f: f['release_date'],
        reverse=True,
    )
    if not films_sorted:
        return None

    latest_date = films_sorted[0]['release_date']
    this_week = sorted(
        [f for f in films_sorted if f.get('release_date') == latest_date],
        key=lambda f: ((f.get('youtube_views') or 0), attention_score(f)),
        reverse=True,
    )

    film_objects = []
    missing_manual = []
    missing_autofillable = []
    anomalies = []
    ready_titles = []

    for rank, film in enumerate(this_week, start=1):
        title = film.get('title')
        missing = []
        if film.get('tiktok') is None:
            missing.append('tiktok')
        if film.get('google_trends') is None:
            missing.append('google_trends')
        if film.get('nobar') is None:
            missing.append('nobar')
        if film.get('youtube_views') in (None, 0):
            missing.append('youtube_views')
        if film.get('youtube_views', 0) > 0 and not film.get('youtube_url'):
            missing.append('youtube_url')

        human_missing, autofillable_missing, other_missing = classify_missing(missing)

        film_anomalies = []
        if film.get('buzz_level') == 'TINGGI' and (film.get('youtube_views') or 0) < 500000:
            film_anomalies.append('buzz_threshold_mismatch')

        if human_missing:
            missing_manual.append({'title': title, 'fields': human_missing})
        if autofillable_missing or other_missing:
            missing_autofillable.append({'title': title, 'fields': autofillable_missing + other_missing})
        if film_anomalies:
            anomalies.append({'title': title, 'issues': film_anomalies})
        if not human_missing and not autofillable_missing and not other_missing and not film_anomalies:
            ready_titles.append(title)

        film_objects.append({
            'rank': rank,
            'title': title,
            'youtube_views': film.get('youtube_views'),
            'buzz_level': film.get('buzz_level'),
            'attention_score': attention_score(film),
            'missing_human_inputs': human_missing,
            'missing_autofillable_inputs': autofillable_missing,
            'missing_other_inputs': other_missing,
            'anomalies': film_anomalies,
            'ready': not human_missing and not autofillable_missing and not other_missing and not film_anomalies,
        })

    return {
        'week_of': latest_date,
        'film_count': len(this_week),
        'films_in_scope': [f.get('title') for f in this_week],
        'priority_order': [f.get('title') for f in this_week],
        'film_status': film_objects,
        'missing_human_inputs': missing_manual,
        'missing_autofillable_inputs': missing_autofillable,
        'anomalies': anomalies,
        'ready_titles': ready_titles,
        'ready_count': len(ready_titles),
        'summary_ready': len(ready_titles) == len(this_week) and len(this_week) > 0,
        'operator_summary': build_operator_summary(this_week, ready_titles, missing_manual, anomalies),
    }


def main():
    films, meta = load_data()
    if films is None:
        print_issues()
        return 1

    schedule_map = load_schedule_map()
    validate_top_level(films, meta)
    validate_duplicates(films)

    for idx, film in enumerate(films):
        validate_film(film, idx, schedule_map)

    weekly_state = build_weekly_state(films)
    if weekly_state is not None:
        WEEKLY_STATE_PATH.write_text(json.dumps(weekly_state, indent=2, ensure_ascii=False) + '\n')

    print_issues()
    return 1 if any(i['severity'] == 'ERROR' for i in issues) else 0


def print_issues():
    errors = [i for i in issues if i['severity'] == 'ERROR']
    warns = [i for i in issues if i['severity'] == 'WARN']
    print(f'Validation complete: {len(errors)} error(s), {len(warns)} warning(s)')
    for item in issues:
        parts = [item['severity']]
        if item.get('film'):
            parts.append(f"film={item['film']}")
        if item.get('field'):
            parts.append(f"field={item['field']}")
        prefix = ' | '.join(parts)
        print(f'- {prefix}: {item["message"]}')


if __name__ == '__main__':
    sys.exit(main())
