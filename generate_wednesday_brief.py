#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILMS_PATH = ROOT / 'films.json'
SCHEDULE_PATH = ROOT / 'films_schedule.json'
OPERATING_WEEK_PATH = ROOT / 'operating_week.json'
WEEKLY_STATE_PATH = ROOT / 'weekly_state.json'


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_films():
    data = load_json(FILMS_PATH)
    films = data.get('films', []) if isinstance(data, dict) else data
    return {film['title']: film for film in films if isinstance(film, dict) and isinstance(film.get('title'), str)}


def load_schedule():
    if not SCHEDULE_PATH.exists():
        return []
    data = load_json(SCHEDULE_PATH)
    return data.get('films', []) if isinstance(data, dict) else data


def format_views(value):
    if value is None:
        return '-'
    if value >= 1_000_000:
        return f'{value / 1_000_000:.2f}Jt'.rstrip('0').rstrip('.')
    if value >= 1_000:
        return f'{round(value / 1_000):.0f}Rb'
    return str(value)


def format_week_label(value):
    if value is None:
        return ''
    return str(value).replace('May', 'Mei')


def format_gt(film):
    value = film.get('google_trends')
    if value is None:
        return 'pending'
    suffix = '*' if film.get('gt_entity_type') == 'search_term' else ''
    return f'{value}{suffix}'


def gt_benchmark_line(films):
    titles = {film.get('gt_benchmark_title') for film in films if film.get('gt_benchmark_title')}
    values = {film.get('gt_benchmark_value') for film in films if film.get('gt_benchmark_value') is not None}
    if len(titles) != 1:
        return None
    title = next(iter(titles))
    if len(values) == 1:
        return f'Benchmark GT: {title} = {next(iter(values))}, Indonesia, past week, web search.'
    return f'Benchmark GT: {title}, Indonesia, past week, web search.'


def gt_caveat(films):
    lower_confidence = [film['title'] for film in films if film.get('gt_entity_type') == 'search_term']
    if not lower_confidence:
        return None
    if len(lower_confidence) == 1:
        return f"*Catatan: Google Trends belum mengenali {lower_confidence[0]} sebagai film, jadi angka GT-nya saya baca hati-hati."
    joined = ', '.join(lower_confidence)
    return f"*Catatan: Google Trends belum mengenali {joined} sebagai film, jadi angka GT-nya saya baca hati-hati."


def describe_week(films):
    if not films:
        return ['Tidak ada film dalam operating slate.']

    lines = []
    titles = {film.get('title') for film in films}
    if {'Tumbal Proyek', 'Semua Akan Baik-Baik Saja', 'Silent Dance'}.issubset(titles):
        by_title = {film['title']: film for film in films}
        tumpal = by_title['Tumbal Proyek']
        semua = by_title['Semua Akan Baik-Baik Saja']
        silent = by_title['Silent Dance']
        lines.append('Belum ada film yang terlihat buzz tinggi.')
        lines.append(
            f"Tumbal Proyek paling balance: TikTok {tumpal.get('tiktok')}, "
            f"GT {tumpal.get('google_trends')}, YouTube {format_views(tumpal.get('youtube_views'))}, "
            f"plus horror + {tumpal.get('ph')} lebih natural utk SAMS."
        )
        lines.append(
            f"Semua Akan Baik-Baik Saja punya trailer reach lebih besar, tapi TikTok {semua.get('tiktok')} "
            f"+ GT {format_gt(semua)} bikin active demand-nya terlihat lebih lemah."
        )
        lines.append(
            f"Silent Dance saya baca sebagai low-priority/test allocation dulu: YouTube {format_views(silent.get('youtube_views'))}, "
            f"TikTok {silent.get('tiktok')}, dan GT masih pending."
        )
        return lines

    if not any(film.get('buzz_level') == 'TINGGI' for film in films):
        lines.append('Dua-duanya belum terlihat buzz tinggi.' if len(films) == 2 else 'Belum ada film yang terlihat buzz tinggi.')

    yt_leader = max(films, key=lambda film: film.get('youtube_views') or 0)
    lines.append(f"{yt_leader['title']} lebih kuat di trailer.")

    gt_films = [film for film in films if film.get('google_trends') is not None]
    gt_leader = max(gt_films, key=lambda film: film.get('google_trends') or 0) if gt_films else None
    if gt_leader:
        genre = (gt_leader.get('genre') or '').lower()
        ph = gt_leader.get('ph')
        fit = ''
        if 'horor' in genre and ph:
            fit = f' dan lebih cocok ke SAMS dari sisi horror + {ph}'
        elif 'horor' in genre:
            fit = ' dan lebih cocok ke SAMS dari sisi horror'
        lines.append(f"{gt_leader['title']} lebih kuat di search interest{fit}.")
        lines.append(f"Untuk sementara saya lebih perhatikan {gt_leader['title']}, tapi belum final sebelum TikTok masuk.")
    else:
        lines.append('Belum ada ranking final sebelum TikTok dan Google Trends masuk.')

    return lines


def relevant_exclusions(schedule, operating_week):
    week_start = operating_week.get('week_start')
    titles = set(operating_week.get('films_releasing', []))
    exclusions = []
    for item in schedule:
        if item.get('date') != week_start:
            continue
        title = item.get('title')
        ph = item.get('production_house') or ''
        if title not in titles and 'rapi' in ph.lower():
            exclusions.append(title)
    return exclusions


def main():
    films_by_title = load_films()
    schedule = load_schedule()
    operating_week = load_json(OPERATING_WEEK_PATH)
    weekly_state = load_json(WEEKLY_STATE_PATH) if WEEKLY_STATE_PATH.exists() else {}

    titles = operating_week.get('films_releasing', [])
    films = [films_by_title[title] for title in titles if title in films_by_title]

    print(f"Siang Dias. Update utk rilis {format_week_label(operating_week.get('week_label'))} yang saya track utk SAMS:")
    print('')
    for film in films:
        print(
            f"* {film['title']} — YouTube {format_views(film.get('youtube_views'))} "
            f"({film.get('buzz_level')}), Google Trends {format_gt(film)}"
        )

    benchmark = gt_benchmark_line(films)
    caveat = gt_caveat(films)
    if benchmark or caveat:
        print('')
    if benchmark:
        print(benchmark)
    if caveat:
        print(caveat)

    print('')
    print('*Quick read:*')
    for line in describe_week(films):
        print(line)

    exclusions = relevant_exclusions(schedule, operating_week)
    if exclusions:
        print('')
        for title in exclusions:
            print(f'{title} saya exclude karena RAPI.')

    missing_human = weekly_state.get('missing_human_inputs', [])
    if missing_human:
        print('')
        print('Bisa bantu confirm:')
        print('1. Apakah ada judul lokal lain yang masuk SAMS minggu ini?')
        print('2. Skor TikTok untuk ' + ' dan '.join(group['title'] for group in missing_human) + '?')
        print('')
        print('Makasih.')


if __name__ == '__main__':
    main()
