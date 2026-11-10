"""Decide whether an RA event is dubstep-relevant."""
from collections import Counter

RA_DUBSTEP_GENRE = "dubstep"

# Bass-adjacent RA genres, keyed by lowercase RA name -> display name as RA writes it.
# Order = priority when an event fits several groups: specific genres first,
# the generic "Bass" tag last.
RA_ADJACENT_GENRES = {
    "grime": "Grime",
    "jungle": "Jungle",
    "drum & bass": "Drum & Bass",
    "dub": "Dub",
    "garage": "Garage",
    "uk funky": "UK Funky",
    "footwork": "Footwork",
    "breakbeat": "Breakbeat",
    "bass": "Bass",
}
ADJACENT_ORDER = list(RA_ADJACENT_GENRES.values())

TEXT_KEYWORDS = ("dubstep", "riddim", "brostep", "deathstep", "tearout", "wobble", "140 bpm")


def _ra_genre_names(event):
    return {g["name"].strip().lower() for g in (event.get("genres") or [])}


def _by_priority(keys):
    return [RA_ADJACENT_GENRES[k] for k in RA_ADJACENT_GENRES if k in keys]


def classify_event(event, artist_history_genres_by_id):
    """artist_history_genres_by_id: dict artist_id -> list of RA genre names from that
    artist's past bookings (may contain duplicates).

    Returns a dict with keys:
      confirmed (bool), adjacent (bool), reasons (list[str]),
      groups (list[str]): bass-adjacent genres this event fits, primary first,
      group_source: "event" (the event itself is tagged so) or "artist" (only via
      lineup history) or None.
    """
    reasons = []
    ra_genres = _ra_genre_names(event)

    confirmed = False
    if RA_DUBSTEP_GENRE in ra_genres:
        confirmed = True
        reasons.append("RA-Genre-Tag des Events: Dubstep")

    title = (event.get("title") or "").lower()
    for kw in TEXT_KEYWORDS:
        if kw in title:
            confirmed = True
            reasons.append(f"Titel enthält Keyword '{kw}'")

    for artist in event.get("artists") or []:
        history = [g.strip().lower() for g in artist_history_genres_by_id.get(artist["id"], [])]
        if RA_DUBSTEP_GENRE in history:
            confirmed = True
            count = history.count(RA_DUBSTEP_GENRE)
            reasons.append(f"Artist '{artist['name']}' hat {count}x Dubstep in bisherigen RA-Gigs")

    groups = []
    group_source = None
    event_matches = ra_genres & RA_ADJACENT_GENRES.keys()
    if event_matches:
        # Advertised genres win: group exactly as the promoter tagged it on RA.
        groups = _by_priority(event_matches)
        group_source = "event"
        if not confirmed:
            reasons.append(f"RA-Genre-Tag(s) des Events bass-nah: {', '.join(groups)}")
    elif not confirmed:
        counts = Counter()
        for artist in event.get("artists") or []:
            history = [g.strip().lower() for g in artist_history_genres_by_id.get(artist["id"], [])]
            matched = {g for g in history if g in RA_ADJACENT_GENRES}
            if matched:
                counts.update(g for g in history if g in RA_ADJACENT_GENRES)
                names = ", ".join(_by_priority(matched))
                reasons.append(f"Artist '{artist['name']}' bass-nahe Historie: {names}")
        if counts:
            # Most frequent genre in the lineup's history first, ties by priority.
            prio = list(RA_ADJACENT_GENRES)
            ordered = sorted(counts, key=lambda g: (-counts[g], prio.index(g)))
            groups = [RA_ADJACENT_GENRES[g] for g in ordered]
            group_source = "artist"

    adjacent = (not confirmed) and bool(groups)
    return {
        "confirmed": confirmed,
        "adjacent": adjacent,
        "reasons": reasons,
        "groups": groups,
        "group_source": group_source,
    }
