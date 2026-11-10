"""Render the radar results as a single static HTML page (served via GitHub Pages from docs/)."""
import os
from datetime import datetime
from html import escape

try:
    from zoneinfo import ZoneInfo
    VIENNA = ZoneInfo("Europe/Vienna")
except Exception:  # no tz database available
    VIENNA = None

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTHS = ["Jän", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def _slug(name):
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def _start_time(event):
    st = event.get("startTime") or ""
    # RA gives local wall-clock time like "2026-11-13T23:00:00.000"
    if len(st) >= 16 and st[11:16] != "00:00":
        return st[11:16]
    return None


def _card(event, result):
    d = datetime.fromisoformat(event["date"][:10])
    venue = event["venue"]["name"] if event.get("venue") else "Venue tba"
    artists = [a["name"] for a in event.get("artists") or []]
    url = f"https://ra.co{event['contentUrl']}" if event.get("contentUrl") else None
    start = _start_time(event)
    ra_genres = [g["name"] for g in event.get("genres") or []]

    chips = "".join(f'<span class="chip">{escape(g)}</span>' for g in ra_genres)
    if result["group_source"] == "artist":
        chips += (f'<span class="chip ghost" title="Event selbst nicht so getaggt">'
                  f'{escape(" / ".join(result["groups"]))} via Lineup</span>')

    title = escape(event["title"])
    title_html = f'<a href="{escape(url)}" target="_blank" rel="noopener">{title}</a>' if url else title
    meta = escape(venue) + (f" · ab {start}" if start else "")
    lineup = escape(", ".join(artists)) if artists else '<span class="muted">Kein Lineup gelistet</span>'
    reasons = "".join(f"<li>{escape(r)}</li>" for r in result["reasons"])

    return f"""
      <article class="card" data-groups="{escape(' '.join(_slug(g) for g in result['groups']))}">
        <div class="date"><span class="wd">{WEEKDAYS[d.weekday()]}</span><span class="day">{d.day}</span><span class="mon">{MONTHS[d.month - 1]}</span></div>
        <div class="body">
          <h3>{title_html}</h3>
          <p class="meta">{meta}</p>
          <p class="lineup">{lineup}</p>
          <div class="chips">{chips}</div>
          <details><summary>Warum hier?</summary><ul>{reasons}</ul></details>
        </div>
      </article>"""


def render(generated_at, confirmed, adjacent_groups):
    local = generated_at.astimezone(VIENNA) if VIENNA else generated_at
    stamp = f"{WEEKDAYS[local.weekday()]}, {local.day}. {MONTHS[local.month - 1]} {local.year}, {local:%H:%M}"
    n_adj = sum(len(items) for _, items in adjacent_groups)

    confirmed_html = "".join(_card(ev, r) for ev, r in confirmed) or '<p class="empty">Aktuell keine bestätigten Dubstep-Events.</p>'

    filters = f'<button class="filter active" data-filter="all">Alle <b>{n_adj}</b></button>'
    filters += "".join(
        f'<button class="filter" data-filter="{_slug(g)}">{escape(g)} <b>{len(items)}</b></button>'
        for g, items in adjacent_groups
    )
    groups_html = "".join(
        f'<section class="group" data-group="{_slug(g)}"><h3 class="group-title">{escape(g)} '
        f'<span class="count">{len(items)}</span></h3>'
        + "".join(_card(ev, r) for ev, r in items) + "</section>"
        for g, items in adjacent_groups
    ) or '<p class="empty">Aktuell keine.</p>'

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wien Dubstep Radar</title>
<meta name="description" content="Dubstep- und bass-nahe Events in Wien, täglich aus Resident Advisor gescannt.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔊</text></svg>">
<style>
  :root {{
    --bg: #0d0e12; --surface: #16181f; --surface2: #1e212a; --border: #2a2e3a;
    --text: #e8e9ee; --muted: #8b90a0; --accent: #b6f23d; --accent-ink: #0d0e12;
    --bass: #7aa7ff;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f4f5f7; --surface: #ffffff; --surface2: #eceef2; --border: #d9dce3;
      --text: #15171c; --muted: #5d6270; --accent: #4d7c00; --accent-ink: #ffffff;
      --bass: #2c5fd6;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 32px 16px 64px; }}
  header h1 {{ margin: 0; font-size: 2rem; letter-spacing: -0.02em; }}
  header h1 span {{ color: var(--accent); }}
  header p {{ margin: 4px 0 0; color: var(--muted); font-size: .9rem; }}
  h2 {{ margin: 40px 0 12px; font-size: 1.15rem; display: flex; align-items: baseline; gap: 10px; }}
  h2 .count, .group-title .count {{ font-size: .8rem; color: var(--muted); font-weight: 500; }}
  .hint {{ color: var(--muted); font-size: .85rem; margin: -6px 0 14px; }}
  .card {{ display: flex; gap: 14px; background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 14px; margin-bottom: 10px; }}
  #dubstep .card {{ border-left: 3px solid var(--accent); }}
  .date {{ flex: 0 0 52px; display: flex; flex-direction: column; align-items: center;
    background: var(--surface2); border-radius: 8px; padding: 6px 0; height: fit-content; }}
  .date .wd, .date .mon {{ font-size: .7rem; text-transform: uppercase; color: var(--muted); letter-spacing: .05em; }}
  .date .day {{ font-size: 1.4rem; font-weight: 700; line-height: 1.1; }}
  .body {{ min-width: 0; flex: 1; }}
  .card h3 {{ margin: 0; font-size: 1rem; line-height: 1.3; overflow-wrap: anywhere; }}
  .card h3 a {{ color: inherit; text-decoration: none; }}
  .card h3 a:hover {{ text-decoration: underline; }}
  .meta {{ margin: 2px 0 6px; color: var(--muted); font-size: .88rem; }}
  .lineup {{ margin: 0 0 8px; font-size: .9rem; overflow-wrap: anywhere; }}
  .muted {{ color: var(--muted); }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .chip {{ font-size: .75rem; padding: 2px 8px; border-radius: 99px; background: var(--surface2);
    border: 1px solid var(--border); }}
  .chip.ghost {{ border-style: dashed; color: var(--bass); }}
  details {{ margin-top: 8px; font-size: .8rem; color: var(--muted); }}
  summary {{ cursor: pointer; }}
  details ul {{ margin: 4px 0 0; padding-left: 18px; }}
  .filters {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
  .filter {{ font: inherit; font-size: .85rem; padding: 6px 12px; border-radius: 99px; cursor: pointer;
    background: var(--surface); color: var(--text); border: 1px solid var(--border); }}
  .filter b {{ font-weight: 600; color: var(--muted); margin-left: 2px; }}
  .filter.active {{ background: var(--bass); border-color: var(--bass); color: #fff; }}
  .filter.active b {{ color: inherit; opacity: .8; }}
  .group-title {{ margin: 22px 0 10px; font-size: .95rem; color: var(--bass); display: flex; gap: 8px; align-items: baseline; }}
  .empty {{ color: var(--muted); }}
  footer {{ margin-top: 48px; color: var(--muted); font-size: .8rem; }}
  footer a {{ color: inherit; }}
</style>
</head>
<body>
<main>
  <header>
    <h1>Wien <span>Dubstep</span> Radar</h1>
    <p>Stand: {escape(stamp)} · nächste 60 Tage · Quelle: Resident Advisor</p>
  </header>

  <section id="dubstep">
    <h2>Dubstep <span class="count">{len(confirmed)}</span></h2>
    {confirmed_html}
  </section>

  <section id="bass">
    <h2>Bass-nah <span class="count">{n_adj}</span></h2>
    <p class="hint">Gruppiert nach dem Genre, mit dem das Event auf RA ausgeschrieben ist. Gestrichelt = Event ungetaggt, Genre stammt aus der Gig-Historie des Lineups.</p>
    <div class="filters">{filters}</div>
    {groups_html}
  </section>

  <footer>Wird täglich automatisch aktualisiert. Daten von <a href="https://ra.co/events/at/vienna">ra.co</a>.</footer>
</main>
<script>
  document.querySelectorAll(".filter").forEach(btn => btn.addEventListener("click", () => {{
    document.querySelectorAll(".filter").forEach(b => b.classList.toggle("active", b === btn));
    const f = btn.dataset.filter;
    document.querySelectorAll("#bass .group").forEach(s => {{
      s.hidden = f !== "all" && s.dataset.group !== f;
    }});
  }}));
</script>
</body>
</html>
"""


def write_site(path, generated_at, confirmed, adjacent_groups):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(generated_at, confirmed, adjacent_groups))
    # Tell GitHub Pages to serve files as-is (no Jekyll processing).
    open(os.path.join(os.path.dirname(path), ".nojekyll"), "a").close()
