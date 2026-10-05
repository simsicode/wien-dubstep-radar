"""Client for Resident Advisor's public GraphQL endpoint."""
import json
import urllib.request
from datetime import datetime, timedelta, timezone

RA_GRAPHQL_URL = "https://ra.co/graphql"
USER_AGENT = "Mozilla/5.0"
VIENNA_AREA_ID = 450

ARTIST_HISTORY_QUERY = """
query ($id: ID!, $limit: Int) {
  artist(id: $id) {
    events(limit: $limit, type: LATEST) {
      genres { name }
    }
  }
}
"""

LISTINGS_QUERY = """
query ($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
  eventListings(filters: $filters, pageSize: $pageSize, page: $page) {
    totalResults
    data {
      event {
        id
        title
        date
        contentUrl
        venue { id name }
        artists { id name }
        genres { id name }
      }
    }
  }
}
"""


def _post(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        RA_GRAPHQL_URL,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if "errors" in payload:
        raise RuntimeError(f"RA GraphQL error: {payload['errors']}")
    return payload["data"]


def fetch_vienna_events(days_ahead=60, area_id=VIENNA_AREA_ID):
    """Returns a list of event dicts for Vienna within [today, today+days_ahead]."""
    today = datetime.now(timezone.utc).date()
    date_from = today.isoformat()
    date_to = (today + timedelta(days=days_ahead)).isoformat()

    filters = {
        "areas": {"eq": area_id},
        "listingDate": {
            "gte": f"{date_from}T00:00:00.000Z",
            "lte": f"{date_to}T00:00:00.000Z",
        },
    }

    events = []
    seen_ids = set()
    page = 1
    page_size = 50
    while True:
        data = _post(LISTINGS_QUERY, {"filters": filters, "pageSize": page_size, "page": page})
        listings = data["eventListings"]["data"]
        if not listings:
            break
        for item in listings:
            ev = item["event"]
            if ev["id"] in seen_ids:
                continue
            seen_ids.add(ev["id"])
            events.append(ev)
        if len(listings) < page_size:
            break
        page += 1
    return events


def fetch_artist_genre_history(artist_id, limit=20):
    """Returns a list of RA genre names (with duplicates) from an artist's recent bookings."""
    data = _post(ARTIST_HISTORY_QUERY, {"id": artist_id, "limit": limit})
    artist = data.get("artist")
    if not artist:
        return []
    genres = []
    for ev in artist.get("events") or []:
        for g in ev.get("genres") or []:
            genres.append(g["name"])
    return genres
