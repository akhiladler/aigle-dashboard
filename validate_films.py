#!/usr/bin/env python3
import json
import math
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
FILMS_PATH = ROOT / 'films.json'
SCHEDULE_PATH = ROOT / 'films_schedule.json'
OPERATING_WEEK_PATH = ROOT / 'operating_week.json'
WEEKLY_STATE_PATH = ROOT / 'weekly_state.json'
CONFIG_PATH = ROOT / 'pipeline_config.json'
PH_TIERS_PATH = ROOT / 'ph-tiers.json'

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
OPTIONAL_DATE_FIELDS = ['gt_capture_date']
OPTIONAL_URL_FIELDS = ['youtube_url']
OPTIONAL_BOOL_FIELDS = ['google_trends_pending']
MANUAL_FIELDS = {'tiktok'}
AUTOFILLABLE_FIELDS = {'google_trends', 'youtube_views', 'youtube_url'}
PENDING_GT_REQUIRED_FIELDS = ['gt_benchmark_title', 'gt_capture_context', 'gt_capture_stage']

issues = []


def add(severity, message, film=None, field=None):
    issues.append({
        'severity': severity,
        'message': message,
        'film': film,
        'field': field,
    })


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def valid_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False


def parse_date(value):
    return date.fromisoformat(value)


def parse_iso_datetime(value):
    return datetime.fromisoformat(value)


def rounded_ratio_ok(raw_num, raw_den, stored, tolerance=0.15):
    if raw_num is None or raw_den in (None, 0) or stored is None:
        return True
    calc = round(raw_num / raw_den, 1)
    return abs(calc - stored) <= tolerance


def load_config():
    return load_json(CONFIG_PATH)


def load_ph_tiers():
    data = load_json(PH_TIERS_PATH)
    tiers = set((data.get('tiers') or {}).keys())
    tiers.add('GOV')
    return tiers


def load_data():
    try:
        data = load_json(FILMS_PATH)
    except Exception as exc:
        add('ERROR', f'Failed to read/parse films.json: {exc}')
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
    except Exception as exc:
        add('WARN', f'Failed to read/parse films_schedule.json: {exc}', field='films_schedule.json')
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
        film_date = item.get('date')
        if isinstance(title, str) and isinstance(film_date, str):
            schedule[title] = film_date
    return schedule


def load_operating_week(config):
    try:
        payload = load_json(OPERATING_WEEK_PATH)
    except Exception as exc:
        add('ERROR', f'Failed to read/parse operating_week.json: {exc}', field='operating_week.json')
        return None

    required_fields = ['week_label', 'week_start', 'films_releasing', 'updated_at', 'updated_by']
    for field in required_fields:
        if field not in payload:
            add('ERROR', f'Missing operating_week field: {field}', field='operating_week.json')

    week_start = payload.get('week_start')
    if not isinstance(week_start, str) or not DATE_RE.match(week_start):
        add('ERROR', 'operating_week.week_start must match YYYY-MM-DD', field='operating_week.json')
    else:
        try:
            parse_date(week_start)
        except ValueError:
            add('ERROR', 'operating_week.week_start is not a valid calendar date', field='operating_week.json')

    films_releasing = payload.get('films_releasing')
    if not isinstance(films_releasing, list) or not films_releasing or not all(isinstance(item, str) and item.strip() for item in films_releasing):
        add('ERROR', 'operating_week.films_releasing must be a non-empty array of strings', field='operating_week.json')

    updated_at = payload.get('updated_at')
    if isinstance(updated_at, str):
        try:
            updated_at_dt = parse_iso_datetime(updated_at)
            today = datetime.now(ZoneInfo(config['timezone'])).date()
            age_days = (today - updated_at_dt.date()).days
            if age_days > config['operating_week']['stale_after_days']:
                add('ERROR', f'operating_week.json is stale ({age_days} days old)', field='operating_week.json')
        except ValueError:
            add('ERROR', 'operating_week.updated_at must be a valid ISO datetime', field='operating_week.json')
    else:
        add('ERROR', 'operating_week.updated_at must be a string', field='operating_week.json')

    return payload


def validate_top_level(films, meta):
    if isinstance(meta, dict) and 'total_films' in meta:
        if meta['total_films'] != len(films):
            add('ERROR', f"meta.total_films={meta['total_films']} does not match films.length={len(films)}", field='meta.total_films')


def validate_film(film, idx, schedule_map, valid_ph_tiers):
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
                parse_date(release_date)
            except ValueError:
                add('ERROR', 'release_date is not a valid calendar date', film=title, field='release_date')

    if film.get('ph_tier') not in valid_ph_tiers:
        add('ERROR', f"Invalid ph_tier: {film.get('ph_tier')}", film=title, field='ph_tier')

    if film.get('buzz_level') not in BUZZ_LEVELS:
        add('ERROR', f"Invalid buzz_level: {film.get('buzz_level')}", film=title, field='buzz_level')

    if film.get('calendar') not in CALENDAR_VALUES:
        add('ERROR', f"Invalid calendar: {film.get('calendar')}", film=title, field='calendar')

    for field in OPTIONAL_BOOL_FIELDS:
        value = film.get(field)
        if value is not None and not isinstance(value, bool):
            add('ERROR', f'{field} must be true, false, or null', film=title, field=field)

    for field in OPTIONAL_URL_FIELDS:
        value = film.get(field)
        if value is not None and (not isinstance(value, str) or not valid_url(value)):
            add('ERROR', f'{field} must be a valid http/https URL', film=title, field=field)

    for field in OPTIONAL_DATE_FIELDS:
        value = film.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not DATE_RE.match(value):
            add('ERROR', f'{field} must match YYYY-MM-DD', film=title, field=field)
            continue
        try:
            parse_date(value)
        except ValueError:
            add('ERROR', f'{field} is not a valid calendar date', film=title, field=field)

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
    gt_pending = film.get('google_trends_pending') is True
    if gt is not None and is_number(gt) and not (0 <= gt <= 100):
        add('ERROR', 'google_trends must be between 0 and 100', film=title, field='google_trends')
    if gt_pending and gt is not None:
        add('ERROR', 'google_trends_pending cannot be true when google_trends already has a score', film=title, field='google_trends_pending')
    if gt_pending:
        for field in PENDING_GT_REQUIRED_FIELDS:
            value = film.get(field)
            if not isinstance(value, str) or not value.strip():
                add('ERROR', f'{field} is required when google_trends_pending=true', film=title, field=field)

    nobar = film.get('nobar')
    if nobar is not None and not isinstance(nobar, bool):
        add('ERROR', 'nobar must be true, false, or null', film=title, field='nobar')

    views = film.get('youtube_views')
    buzz = film.get('buzz_level')
    if is_number(views) and buzz in BUZZ_LEVELS:
        expected = 'TINGGI' if views >= 500000 else 'SEDANG' if views >= 100000 else 'RENDAH'
        if buzz != expected:
            add('ERROR', f'buzz_level={buzz} contradicts youtube_views={views} (expected {expected})', film=title, field='buzz_level')
        if views > 0 and not film.get('youtube_url'):
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

    tiktok = film.get('tiktok')
    if is_number(tiktok):
        score += tiktok / 10.0

    trends = film.get('google_trends')
    if is_number(trends):
        score += min(trends / 50.0, 2)
    return round(score, 2)


def classify_missing(fields):
    human = [field for field in fields if field in MANUAL_FIELDS]
    autofillable = [field for field in fields if field in AUTOFILLABLE_FIELDS]
    other = [field for field in fields if field not in MANUAL_FIELDS and field not in AUTOFILLABLE_FIELDS]
    return human, autofillable, other


def build_operator_summary(titles, ready_for_publish, ready_for_operator, missing_human, missing_auto, missing_titles, pending_signal_inputs):
    if not titles:
        return 'No films in scope.'

    if ready_for_operator:
        return f"All {len(titles)} films are fully ready for Wednesday output."

    if ready_for_publish and missing_human and pending_signal_inputs:
        pending_human = ', '.join(item['title'] for item in missing_human)
        pending_signal_titles = ', '.join(item['title'] for item in pending_signal_inputs)
        return f"Machine side is publish-ready. Human inputs still pending for: {pending_human}. Signal confirmation still pending for: {pending_signal_titles}."

    if ready_for_publish and missing_human:
        pending = ', '.join(item['title'] for item in missing_human)
        return f"Machine side is publish-ready. Human inputs still pending for: {pending}."

    if ready_for_publish and pending_signal_inputs:
        pending_signal_titles = ', '.join(item['title'] for item in pending_signal_inputs)
        return f"Machine side is publish-ready. Signal confirmation still pending for: {pending_signal_titles}."

    if missing_titles:
        return f"Operating week is blocked. Missing film records for: {', '.join(missing_titles)}."

    blocked = ', '.join(item['title'] for item in missing_auto) if missing_auto else 'unknown'
    return f"Machine side is not ready. Missing automated or audit inputs for: {blocked}."


def validate_operating_scope(operating_week, films_by_title):
    week_start = operating_week.get('week_start')
    titles = operating_week.get('films_releasing') or []

    if not isinstance(titles, list):
        return

    for title in titles:
        film = films_by_title.get(title)
        if film is None:
            add('ERROR', 'Film listed in operating_week.json is missing from films.json', film=title, field='operating_week.json')
            continue
        if film.get('release_date') != week_start:
            add('ERROR', f"Film release_date={film.get('release_date')} does not match operating week start={week_start}", film=title, field='release_date')


def build_weekly_state(films_by_title, operating_week, config):
    titles = operating_week.get('films_releasing') or []
    audit_fields = config['wednesday']['audit_fields']
    deadline_local = config['wednesday']['deadline_local']

    film_status = []
    missing_titles = []
    missing_human = []
    missing_auto = []
    missing_audit = []
    pending_signal_inputs = []
    anomalies = []
    ready_for_publish_titles = []
    ready_for_operator_titles = []

    for rank, title in enumerate(titles, start=1):
        film = films_by_title.get(title)
        if film is None:
            missing_titles.append(title)
            continue

        missing = []
        pending_signals = []
        gt_pending = film.get('google_trends_pending') is True
        if film.get('tiktok') is None:
            missing.append('tiktok')
        if film.get('youtube_views') in (None, 0):
            missing.append('youtube_views')
        if film.get('youtube_views', 0) > 0 and not film.get('youtube_url'):
            missing.append('youtube_url')
        if film.get('google_trends') is None:
            if gt_pending:
                pending_missing = [
                    field for field in PENDING_GT_REQUIRED_FIELDS
                    if not film.get(field)
                ]
                if pending_missing:
                    missing.extend(pending_missing)
                else:
                    pending_signals.append('google_trends')
            else:
                missing.append('google_trends')

        audit_missing = []
        if film.get('google_trends') is not None:
            for field in audit_fields:
                if not film.get(field):
                    audit_missing.append(field)

        human_missing, autofillable_missing, other_missing = classify_missing(missing)
        week_anomalies = []
        expected_buzz = 'TINGGI' if (film.get('youtube_views') or 0) >= 500000 else 'SEDANG' if (film.get('youtube_views') or 0) >= 100000 else 'RENDAH'
        if film.get('buzz_level') != expected_buzz:
            week_anomalies.append('buzz_threshold_mismatch')

        if human_missing:
            missing_human.append({'title': title, 'fields': human_missing})
        if autofillable_missing or other_missing:
            missing_auto.append({'title': title, 'fields': autofillable_missing + other_missing})
        if audit_missing:
            missing_audit.append({'title': title, 'fields': audit_missing})
        if pending_signals:
            pending_signal_inputs.append({'title': title, 'fields': pending_signals})
        if week_anomalies:
            anomalies.append({'title': title, 'issues': week_anomalies})

        machine_ready = not autofillable_missing and not other_missing and not audit_missing and not week_anomalies
        operator_ready = machine_ready and not human_missing and not pending_signals

        if machine_ready:
            ready_for_publish_titles.append(title)
        if operator_ready:
            ready_for_operator_titles.append(title)

        film_status.append({
            'rank': rank,
            'title': title,
            'youtube_views': film.get('youtube_views'),
            'buzz_level': film.get('buzz_level'),
            'tiktok': film.get('tiktok'),
            'google_trends': film.get('google_trends'),
            'google_trends_pending': gt_pending,
            'attention_score': attention_score(film),
            'gt_benchmark_title': film.get('gt_benchmark_title'),
            'gt_entity_type': film.get('gt_entity_type'),
            'missing_human_inputs': human_missing,
            'missing_autofillable_inputs': autofillable_missing + other_missing,
            'missing_audit_inputs': audit_missing,
            'pending_signal_inputs': pending_signals,
            'anomalies': week_anomalies,
            'machine_ready': machine_ready,
            'operator_ready': operator_ready,
        })

    ready_for_publish = not missing_titles and len(ready_for_publish_titles) == len(titles)
    ready_for_operator = not missing_titles and len(ready_for_operator_titles) == len(titles)

    return {
        'week_label': operating_week.get('week_label'),
        'week_start': operating_week.get('week_start'),
        'deadline_local': deadline_local,
        'generated_at': datetime.now(ZoneInfo(config['timezone'])).isoformat(timespec='seconds'),
        'films_in_scope': titles,
        'missing_titles': missing_titles,
        'film_status': film_status,
        'missing_human_inputs': missing_human,
        'missing_autofillable_inputs': missing_auto,
        'missing_audit_inputs': missing_audit,
        'pending_signal_inputs': pending_signal_inputs,
        'anomalies': anomalies,
        'ready_for_publish_titles': ready_for_publish_titles,
        'ready_for_operator_titles': ready_for_operator_titles,
        'ready_for_publish': ready_for_publish,
        'ready_for_operator': ready_for_operator,
        'operator_summary': build_operator_summary(
            titles,
            ready_for_publish,
            ready_for_operator,
            missing_human,
            missing_auto + missing_audit,
            missing_titles,
            pending_signal_inputs,
        ),
    }


def print_issues():
    errors = [item for item in issues if item['severity'] == 'ERROR']
    warns = [item for item in issues if item['severity'] == 'WARN']
    print(f'Validation complete: {len(errors)} error(s), {len(warns)} warning(s)')
    for item in issues:
        parts = [item['severity']]
        if item.get('film'):
            parts.append(f"film={item['film']}")
        if item.get('field'):
            parts.append(f"field={item['field']}")
        prefix = ' | '.join(parts)
        print(f'- {prefix}: {item["message"]}')


def main():
    config = load_config()
    valid_ph_tiers = load_ph_tiers()

    films, meta = load_data()
    if films is None:
        print_issues()
        return 1

    operating_week = load_operating_week(config)
    schedule_map = load_schedule_map()

    validate_top_level(films, meta)
    validate_duplicates(films)

    films_by_title = {}
    for idx, film in enumerate(films):
        validate_film(film, idx, schedule_map, valid_ph_tiers)
        if isinstance(film, dict) and isinstance(film.get('title'), str):
            films_by_title[film['title']] = film

    if operating_week is not None:
        validate_operating_scope(operating_week, films_by_title)
        weekly_state = build_weekly_state(films_by_title, operating_week, config)
        WEEKLY_STATE_PATH.write_text(json.dumps(weekly_state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print_issues()
    return 1 if any(item['severity'] == 'ERROR' for item in issues) else 0


if __name__ == '__main__':
    sys.exit(main())
