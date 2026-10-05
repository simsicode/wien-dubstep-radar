"""Decide whether an RA event is dubstep-relevant."""

RA_DUBSTEP_GENRE = "dubstep"
RA_ADJACENT_GENRES = {"bass", "grime", "jungle", "dub"}

TEXT_KEYWORDS = ("dubstep", "riddim", "brostep", "deathstep", "tearout", "wobble", "140 bpm")


def _ra_genre_names(event):
    return {g["name"].strip().lower() for g in (event.get("genres") or [])}


def classify_event(event, artist_history_genres_by_id):
    """artist_history_genres_by_id: dict artist_id -> list of RA genre names from that
    artist's past bookings (may contain duplicates).

    Returns a dict with keys: confirmed (bool), adjacent (bool), reasons (list[str]).
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

    adjacent = (not confirmed) and bool(ra_genres & RA_ADJACENT_GENRES)
    if not adjacent and not confirmed:
        for artist in event.get("artists") or []:
            history = {g.strip().lower() for g in artist_history_genres_by_id.get(artist["id"], [])}
            matched = history & RA_ADJACENT_GENRES
            if matched:
                adjacent = True
                reasons.append(f"Artist '{artist['name']}' bass-nahe Historie: {', '.join(sorted(matched))}")
    elif adjacent:
        matched = ra_genres & RA_ADJACENT_GENRES
        reasons.append(f"RA-Genre-Tag(s) des Events bass-nah: {', '.join(sorted(matched))}")

    return {"confirmed": confirmed, "adjacent": adjacent, "reasons": reasons}
