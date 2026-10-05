"""Scan Vienna RA listings for Dubstep-relevant events and report new finds.

Classification combines three signals, all sourced from Resident Advisor itself:
  1. The event's own RA genre tag(s).
  2. Keyword matches in the event title.
  3. Each lineup artist's genre history across their past RA-listed bookings
     (an artist who has played Dubstep-tagged gigs before is a strong signal,
     even when the upcoming event itself has no genre tag yet).

On stdout, prints a machine-readable summary block starting with a line
"NEW_MATCHES: <n>" followed by one line per newly-confirmed event, so a
calling agent can decide whether to send a push notification.
"""
import json
import os
from datetime import datetime, timedelta, timezone

import ra_client
import classify
from artist_genre_cache import ArtistGenreCache, enrich_artists

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "data", "state.json")
CACHE_PATH = os.path.join(BASE_DIR, "data", "artist_genre_cache.json")
REPORT_PATH = os.path.join(BASE_DIR, "report", "latest.md")

DAYS_AHEAD = 60
STATE_RETENTION_DAYS = 3  # how long past events stay in state before being pruned


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"notified": {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def prune_state(state, today):
    cutoff = today - timedelta(days=STATE_RETENTION_DAYS)
    state["notified"] = {
        eid: date_str
        for eid, date_str in state["notified"].items()
        if datetime.fromisoformat(date_str).date() >= cutoff
    }


def format_event_line(event, result):
    date_str = event["date"][:10]
    venue = event["venue"]["name"] if event.get("venue") else "?"
    artists = ", ".join(a["name"] for a in event.get("artists") or []) or "(kein Lineup gelistet)"
    url = f"https://ra.co{event['contentUrl']}" if event.get("contentUrl") else ""
    tag = "DUBSTEP" if result["confirmed"] else "bass-nah"
    lines = [f"- [{tag}] {date_str} — **{event['title']}** @ {venue}"]
    lines.append(f"  Lineup: {artists}")
    if url:
        lines.append(f"  {url}")
    lines.append(f"  Grund: {'; '.join(result['reasons'])}")
    return "\n".join(lines)


def main():
    today = datetime.now(timezone.utc).date()
    state = load_state()
    cache = ArtistGenreCache(CACHE_PATH)

    events = ra_client.fetch_vienna_events(days_ahead=DAYS_AHEAD)

    all_artists = {}
    for ev in events:
        for a in ev.get("artists") or []:
            all_artists[a["id"]] = a
    genres_by_artist_id = enrich_artists(list(all_artists.values()), cache)

    confirmed_events = []
    adjacent_events = []
    for ev in events:
        result = classify.classify_event(ev, genres_by_artist_id)
        if result["confirmed"]:
            confirmed_events.append((ev, result))
        elif result["adjacent"]:
            adjacent_events.append((ev, result))

    confirmed_events.sort(key=lambda pair: pair[0]["date"])
    adjacent_events.sort(key=lambda pair: pair[0]["date"])

    new_matches = [
        (ev, result) for ev, result in confirmed_events if ev["id"] not in state["notified"]
    ]

    for ev, _ in confirmed_events:
        state["notified"][ev["id"]] = ev["date"][:10]
    prune_state(state, today)
    save_state(state)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Wien Dubstep Radar\n\nStand: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"## Bestätigte Dubstep-Events ({len(confirmed_events)})\n\n")
        if confirmed_events:
            for ev, result in confirmed_events:
                f.write(format_event_line(ev, result) + "\n\n")
        else:
            f.write("Aktuell keine.\n\n")
        f.write(f"## Bass-nahe Events, nicht eindeutig Dubstep ({len(adjacent_events)})\n\n")
        if adjacent_events:
            for ev, result in adjacent_events:
                f.write(format_event_line(ev, result) + "\n\n")
        else:
            f.write("Aktuell keine.\n\n")

    print(f"NEW_MATCHES: {len(new_matches)}")
    for ev, result in new_matches:
        date_str = ev["date"][:10]
        venue = ev["venue"]["name"] if ev.get("venue") else "?"
        print(f"- {date_str} {ev['title']} @ {venue} ({'; '.join(result['reasons'])})")
    print(f"TOTAL_CONFIRMED_UPCOMING: {len(confirmed_events)}")
    print(f"TOTAL_ADJACENT_UPCOMING: {len(adjacent_events)}")
    print(f"ARTISTS_IN_CACHE: {len(cache.data)}")


if __name__ == "__main__":
    main()
