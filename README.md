# Wien Dubstep Radar

Scannt Resident Advisor (RA) für Wien (`areaId=450`) regelmäßig nach Dubstep-relevanten
Events, auch wenn sie von den Promotern nicht als solche getaggt sind.

## Wie klassifiziert wird

Drei Signale, alle direkt aus RAs eigener GraphQL-API (`ra.co/graphql`):

1. **Event-Genre-Tag** — RA erlaubt Promotern, Events mit Genres zu taggen (z.B. "Dubstep",
   id `24`). Direkt, aber selten gepflegt für kleinere Partys.
2. **Titel-Keywords** — Begriffe wie "dubstep", "riddim", "wobble" im Event-Titel.
3. **Artist-Historie** — Für jeden Lineup-Artist werden die Genre-Tags seiner letzten RA-Gigs
   (weltweit) nachgeschlagen. Hat ein Artist schon öfter auf Dubstep-Partys gespielt, ist das
   ein starkes Signal, auch wenn das konkrete Event (noch) ungetaggt ist.

Events mit RA-Genre-Tags "Bass", "Grime", "Jungle" oder "Dub" (am Event oder in der
Artist-Historie), aber ohne konkretes Dubstep-Signal, landen als "bass-nah" in einer
separaten Sektion des Reports — spannend für die Szene, aber nicht sicher Dubstep.

Spotify wurde bewusst **nicht** verwendet: die Artist-`genres`-Felder der Spotify-API liefern
seit Ende 2024 plattformweit leere Listen zurück (getestet u.a. mit Skrillex) und sind damit
für diesen Zweck unbrauchbar.

## Dateien

- `ra_client.py` — GraphQL-Queries gegen `ra.co/graphql` (Event-Listings, Artist-Historie).
- `artist_genre_cache.py` — Cached die Genre-Historie pro Artist-ID (`data/artist_genre_cache.json`).
- `classify.py` — Entscheidet "confirmed" (Dubstep) vs. "adjacent" (bass-nah) pro Event.
- `main.py` — Orchestriert den Lauf, pflegt `data/state.json` (bereits gemeldete Event-IDs,
  um keine Doppel-Benachrichtigungen zu schicken) und schreibt `report/latest.md`.

## Lokal ausführen

```bash
python3 main.py
```

Kein `pip install` nötig — nur Python-Standardbibliothek. Gibt auf stdout u.a.
`NEW_MATCHES: <n>` aus (Events, die seit dem letzten Lauf neu als Dubstep bestätigt wurden).

## Automatisierung

Läuft als Claude Code Cloud-Routine (täglich), die `main.py` ausführt, bei neuen Treffern eine
Push-Notification schickt und die aktualisierten `data/`- und `report/`-Dateien committet.
