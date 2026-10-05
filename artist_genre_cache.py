"""On-disk cache of an artist's RA genre-history (from their past bookings)."""
import json
import os
import time

import ra_client


class ArtistGenreCache:
    def __init__(self, path):
        self.path = path
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def get(self, artist_id):
        return self.data.get(artist_id)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2, sort_keys=True)


def enrich_artists(artists, cache, rate_limit_sleep=0.15):
    """artists: list of {id, name} dicts. Returns dict artist_id -> list of genre names (history).

    Mutates and saves the cache for any artist not already present.
    """
    result = {}
    changed = False
    for artist in artists:
        aid = artist["id"]
        cached = cache.get(aid)
        if cached is not None:
            result[aid] = cached["genres"]
            continue
        try:
            genres = ra_client.fetch_artist_genre_history(aid)
        except Exception:
            genres = []
        cache.data[aid] = {"name": artist["name"], "genres": genres, "fetched_at": int(time.time())}
        result[aid] = genres
        changed = True
        time.sleep(rate_limit_sleep)

    if changed:
        cache.save()
    return result
