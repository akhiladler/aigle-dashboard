import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
}

QUERY_OVERRIDES: Dict[str, List[str]] = {
    "AIN": [
        "AIN official trailer film 2026",
        "AIN official trailer 2026",
    ],
    "SHAKA OH SHAKA": [
        "SHAKA OH SHAKA official trailer",
        "SHAKA OH SHAKA trailer 2026",
    ],
    "The Bell: Panggilan untuk Mati": [
        "The Bell Panggilan untuk Mati official trailer",
        "The Bell official trailer Indonesia 2026",
    ],
    "Crocodile Tears": [
        "Crocodile Tears official trailer 2026",
        "Crocodile Tears trailer Indonesia 2026",
    ],
}

CHANNEL_HINTS: Dict[str, List[str]] = {
    "MVP Pictures": ["mvp pictures", "mvp pictures id", "cinema 21"],
    "Starvision Plus": ["starvisionplus", "starvision plus", "starvision"],
    "Palari Films": ["palari", "cinema 21", "cgv"],
    "Multi Buana Kreasindo": ["mbk productions", "cinema 21", "sinemata"],
}

VIDEO_ID_RE = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')
DETAILS_RE = re.compile(
    r'playerOverlayVideoDetailsRenderer":\{"title":\{"simpleText":"([^"]+)"\},'
    r'"subtitle":\{"runs":\[\{"text":"([^"]+)"\},\{"text":"   "\},'
    r'\{"text":"([^"]+)"\},\{"text":"   "\},\{"text":"([^"]+)"\}'
)


def normalize(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    lowered = lowered.replace("\\u0026", "&")
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def score_candidate(film_title: str, ph: str, title: str, channel: str, published: str) -> int:
    film_norm = normalize(film_title)
    candidate_norm = normalize(title)
    channel_norm = normalize(channel)
    score = 0
    channel_match = False

    if film_norm and film_norm in candidate_norm:
        score += 80

    film_tokens = [token for token in film_norm.split() if len(token) > 2]
    matched = sum(1 for token in film_tokens if token in candidate_norm)
    score += matched * 8

    if "official trailer" in candidate_norm:
        score += 40
    elif "trailer" in candidate_norm:
        score += 20
    else:
        score -= 35

    if "teaser" in candidate_norm:
        score -= 12
    if any(
        word in candidate_norm
        for word in (
            "review",
            "reaction",
            "recap",
            "ending explained",
            "press conference",
            "conference",
            "interview",
            "cast",
            "podcast",
            "live musik",
            "behind the scenes",
            "scene",
            "clip",
        )
    ):
        score -= 40
    if any(word in candidate_norm for word in ("deutsch", "german", "offizieller")):
        score -= 20

    for hint in CHANNEL_HINTS.get(ph, []):
        if hint in channel_norm:
            score += 35
            channel_match = True

    if "cinema 21" in channel_norm:
        score += 8

    if channel_match and "official trailer" in candidate_norm:
        score += 30
    if not channel_match and "official trailer" not in candidate_norm:
        score -= 30

    if any(
        word in candidate_norm
        for word in ("heboh", "salting", "nonton", "keseruan", "hantu", "#film", "#movie")
    ):
        score -= 50
    if "#" in title:
        score -= 20

    if "hour" in published or "day" in published or "week" in published or "month" in published:
        score += 1

    return score


def fetch_search_candidates(query: str, limit: int = 8) -> List[str]:
    url = f"https://www.youtube.com/results?search_query={quote(query)}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    candidates: List[str] = []
    for video_id in VIDEO_ID_RE.findall(response.text):
        if video_id not in candidates:
            candidates.append(video_id)
        if len(candidates) >= limit:
            break
    return candidates


def fetch_video_details(video_id: str) -> Optional[Dict[str, str]]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    match = DETAILS_RE.search(response.text)
    if not match:
        return None
    title, channel, views_text, published = match.groups()
    views_number = int(re.sub(r"[^0-9]", "", views_text) or "0")
    return {
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "views_text": views_text,
        "views": views_number,
        "published": published,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def choose_best_video(film: Dict[str, object]) -> Optional[Dict[str, str]]:
    title = str(film["title"])
    queries = QUERY_OVERRIDES.get(title, [f"{title} official trailer"])
    seen_ids: List[str] = []
    best: Optional[Dict[str, str]] = None
    best_score = -10**9

    for query in queries:
        for video_id in fetch_search_candidates(query):
            if video_id in seen_ids:
                continue
            seen_ids.append(video_id)
            details = fetch_video_details(video_id)
            if not details:
                continue
            score = score_candidate(title, str(film.get("ph") or ""), details["title"], details["channel"], details["published"])
            details["score"] = score
            if score > best_score:
                best = details
                best_score = score

    return best


def buzz_level(views: int) -> str:
    if views >= 500_000:
        return "TINGGI"
    if views >= 100_000:
        return "SEDANG"
    return "RENDAH"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--films-json", default="films.json")
    parser.add_argument("--titles", nargs="*")
    args = parser.parse_args()

    films_path = Path(args.films_json)
    data = json.loads(films_path.read_text(encoding="utf-8"))
    target_titles = set(args.titles or [])

    updated = []
    for film in data.get("films", []):
        if target_titles and film["title"] not in target_titles:
            continue
        best = choose_best_video(film)
        if not best:
            print(f"NO_MATCH | {film['title']}")
            continue
        film["youtube_views"] = best["views"]
        film["youtube_url"] = best["url"]
        film["buzz_level"] = buzz_level(best["views"])
        updated.append((film["title"], best["views"], best["url"], best["channel"], best["title"]))
        print(
            f"UPDATED | {film['title']} | {best['views']} | {best['channel']} | "
            f"{best['title']} | {best['url']}"
        )

    if updated:
        films_path.write_text(json.dumps(data, ensure_ascii=False, indent=6), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
