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

Bass-nahe Events ohne konkretes Dubstep-Signal landen in einer eigenen Sektion, unterteilt
nach dem RA-Genre, mit dem sie ausgeschrieben sind: Grime, Jungle, Drum & Bass, Dub, Garage,
UK Funky, Footwork, Breakbeat, Bass. Hat ein Event mehrere davon, zählt das spezifischere
(das generische "Bass" zuletzt). Ist das Event selbst gar nicht bass-nah getaggt, entscheidet
das häufigste bass-nahe Genre in der Gig-Historie des Lineups (im Report als "via Lineup"
markiert).

Spotify wurde bewusst **nicht** verwendet: die Artist-`genres`-Felder der Spotify-API liefern
seit Ende 2024 plattformweit leere Listen zurück (getestet u.a. mit Skrillex) und sind damit
für diesen Zweck unbrauchbar.

## Dateien

- `ra_client.py` — GraphQL-Queries gegen `ra.co/graphql` (Event-Listings, Artist-Historie).
- `artist_genre_cache.py` — Cached die Genre-Historie pro Artist-ID (`data/artist_genre_cache.json`).
- `classify.py` — Entscheidet "confirmed" (Dubstep) vs. "adjacent" (bass-nah) pro Event.
- `site_gen.py` — Rendert die Ergebnisse als statische Website nach `docs/index.html`.
- `main.py` — Orchestriert den Lauf, pflegt `data/state.json` (bereits gemeldete Event-IDs,
  um keine Doppel-Benachrichtigungen zu schicken) und schreibt `report/latest.md` sowie `docs/index.html`.

## Lokal ausführen

```bash
python3 main.py
```

Kein `pip install` nötig — nur Python-Standardbibliothek. Gibt auf stdout u.a.
`NEW_MATCHES: <n>` aus (Events, die seit dem letzten Lauf neu als Dubstep bestätigt wurden).

## Automatisierung

Läuft als Claude Code Cloud-Routine (täglich), die `main.py` ausführt, bei neuen Treffern eine
Push-Notification schickt und die aktualisierten `data/`- und `report/`-Dateien committet.

## Website

`docs/` wird über GitHub Pages ausgeliefert (Branch `master`, Ordner `/docs`):
https://simsicode.github.io/wien-dubstep-radar/ — aktualisiert sich mit jedem Scan-Commit.
