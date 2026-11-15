"""Generate the profile artwork in ./assets from config.json and real GitHub data.

Standard library only. The activity panel reads the public contribution
calendar through GitHub's GraphQL API, so it needs a token:

    GITHUB_TOKEN=... python scripts/generate.py

Every other asset is built from config.json alone.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

# ── palette: charcoal, copper ember, desert sand ─────────────────────────────
SHELL = "#15110f"
CORE = "#0d0b0a"
PANEL = "#120f0d"
HAIR = "#3a2a22"
HAIR_SOFT = "#261c17"
COPPER = "#e0703a"
AMBER = "#f2a74b"
SAND = "#f6ead9"
MUTED = "#a8968a"
DIM = "#6f6058"

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
EASE = "cubic-bezier(.22,.8,.2,1)"

BASE_CSS = f"""
.label{{font:600 10px {MONO};fill:{AMBER};letter-spacing:2.2px}}
.muted{{font:13px {SANS};fill:{MUTED}}}
.chip{{font:600 11px {SANS};fill:{SAND}}}
.mono{{font:12px {MONO};fill:{MUTED}}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.rise{{animation:rise .9s {EASE} both}}
.fade{{animation:fade 1s {EASE} both}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def defs(extra_css: str = "", extra_defs: str = "") -> str:
    return f"""<defs>
<linearGradient id="rim" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{COPPER}"/><stop offset=".6" stop-color="{AMBER}"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
<radialGradient id="flare" cx="82%" cy="30%" r="60%"><stop stop-color="{COPPER}" stop-opacity=".22"/><stop offset=".5" stop-color="{COPPER}" stop-opacity=".05"/><stop offset="1" stop-color="{CORE}" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
{extra_defs}
<style>{BASE_CSS}{extra_css}</style>
</defs>"""


def frame(w: int, h: int, flare: bool = True) -> str:
    out = f'<rect width="{w}" height="{h}" rx="22" fill="{SHELL}"/>'
    out += f'<rect x="6" y="6" width="{w-12}" height="{h-12}" rx="17" fill="{CORE}" stroke="{HAIR}"/>'
    if flare:
        out += f'<rect x="6" y="6" width="{w-12}" height="{h-12}" rx="17" fill="url(#flare)"/>'
    return out


def header(x: int, y: int, text: str, length: int = 260) -> str:
    return (f'<circle cx="{x}" cy="{y}" r="3.5" fill="{COPPER}" filter="url(#glow)"/>'
            f'<path d="M{x+12} {y}h{length}" stroke="url(#rim)" stroke-width="1.5"/>'
            f'<text x="{x}" y="{y+24}" class="label">{esc(text)}</text>')


def chip(x: float, y: float, text: str, width: float | None = None) -> tuple[str, float]:
    w = width or (len(text) * 6.3 + 20)
    svg = (f'<g transform="translate({x:.1f} {y:.1f})"><rect width="{w:.1f}" height="24" rx="12" fill="#1c1512" stroke="{HAIR}"/>'
           f'<text x="{w/2:.1f}" y="16" text-anchor="middle" class="chip">{esc(text)}</text></g>')
    return svg, w


def star(cx: float, cy: float, r: float) -> str:
    """Eight-point zellige star: two squares, one rotated 45 degrees."""
    s = r * 0.7071
    sq = f"M{cx-s:.2f} {cy-s:.2f}h{2*s:.2f}v{2*s:.2f}h{-2*s:.2f}z"
    dm = f"M{cx:.2f} {cy-r:.2f}L{cx+r:.2f} {cy:.2f}L{cx:.2f} {cy+r:.2f}L{cx-r:.2f} {cy:.2f}z"
    return sq + dm


def write(name: str, svg: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg.strip() + "\n", encoding="utf-8")
    print(f"wrote assets/{name} ({len(svg.encode())} bytes)")


# ── hero ─────────────────────────────────────────────────────────────────────
def hero() -> str:
    c = CONFIG
    w, h = 900, 340
    cx, cy = 728, 168
    css = f"""
.name{{font:700 44px {SANS};fill:{SAND};letter-spacing:-1.4px}}
.role{{font:600 19px {SANS};fill:{COPPER};letter-spacing:-.2px}}
.small{{font:600 9px {MONO};fill:{MUTED};letter-spacing:1.8px}}
.status{{font:600 12px {SANS};fill:{SAND}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes spinr{{to{{transform:rotate(-360deg)}}}}
@keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}
.ring{{transform-origin:{cx}px {cy}px;animation:spin 60s linear infinite}}
.ring2{{transform-origin:{cx}px {cy}px;animation:spinr 90s linear infinite}}
.pulse{{animation:pulse 2.6s ease-in-out infinite}}
"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(c["name"])}, {esc(c["role"])}">',
           defs(css), frame(w, h)]
    # faint zellige lattice behind the emblem
    lattice = "".join(star(x, y, 15) for x in range(560, 900, 56) for y in range(20, 340, 56))
    out.append(f'<path d="{lattice}" fill="none" stroke="{HAIR_SOFT}" stroke-width="1" opacity=".35"/>')
    out.append(header(40, 46, f'{c["role"].upper()}  /  {c["location"].upper()}', 300))
    out.append('<g class="rise">')
    out.append(f'<text x="40" y="132" class="name">{esc(c["name"])}</text>')
    out.append(f'<text x="40" y="166" class="role">{esc(c["stack_line"])}</text>')
    out.append(f'<text x="40" y="198" class="muted" style="font-size:15px">{esc(c["headline"])}</text>')
    out.append('</g>')
    # availability
    out.append('<g class="rise" style="animation-delay:.25s">')
    out.append(f'<text x="40" y="240" class="label">OPEN TO</text>')
    x = 40.0
    for item in c["availability"]:
        svg, cw = chip(x, 252, item)
        out.append(svg)
        x += cw + 10
    out.append(f'<text x="40" y="306" class="small">SPEAKS  {esc(c["languages"].upper())}</text>')
    out.append('</g>')
    # emblem
    out.append('<g class="fade" style="animation-delay:.35s">')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="118" fill="{CORE}" opacity=".85"/>')
    out.append(f'<g class="ring"><circle cx="{cx}" cy="{cy}" r="112" fill="none" stroke="{HAIR}"/>'
               f'<path d="M{cx-112} {cy}A112 112 0 0 1 {cx+79.2} {cy-79.2}" fill="none" stroke="url(#rim)" stroke-width="2.5" stroke-linecap="round"/>'
               f'<circle cx="{cx-112}" cy="{cy}" r="4.5" fill="{COPPER}" filter="url(#glow)"/></g>')
    out.append(f'<g class="ring2"><circle cx="{cx}" cy="{cy}" r="90" fill="none" stroke="{HAIR_SOFT}" stroke-dasharray="2 7"/>'
               f'<circle cx="{cx+90}" cy="{cy}" r="3" fill="{AMBER}"/></g>')
    out.append(f'<path d="{star(cx, cy, 64)}" fill="none" stroke="{COPPER}" stroke-width="1.6" opacity=".9"/>')
    out.append(f'<path d="{star(cx, cy, 44)}" fill="#1a1310" stroke="{HAIR}" stroke-width="1"/>')
    out.append(f'<text x="{cx}" y="{cy+9}" text-anchor="middle" style="font:700 26px {SANS};fill:{SAND};letter-spacing:1px">EA</text>')
    out.append('</g>')
    out.append(f'<circle cx="{w-46}" cy="{h-40}" r="4" fill="#5fd38d" class="pulse"/>')
    out.append(f'<text x="{w-58}" y="{h-36}" text-anchor="end" class="small">AVAILABLE FOR WORK</text>')
    out.append('</svg>')
    return "".join(out)


# ── about (terminal) ─────────────────────────────────────────────────────────
def about() -> str:
    c = CONFIG
    lines = c["about"]
    w = 900
    h = 120 + len(lines) * 22 + 56
    css = f""".prompt{{font:600 13px {MONO};fill:{COPPER}}}.cmd{{font:13px {MONO};fill:{SAND}}}
.out{{font:13.5px {MONO};fill:#d9cbbd}}.key{{font:600 12px {MONO};fill:{AMBER}}}.val{{font:12px {MONO};fill:{MUTED}}}
@keyframes blink{{50%{{opacity:0}}}}.cursor{{animation:blink 1.1s steps(1) infinite}}"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="About {esc(c["name"])}">',
           defs(css), frame(w, h, flare=False)]
    # title bar
    out.append(f'<path d="M6 50h{w-12}" stroke="{HAIR_SOFT}"/>')
    for i, col in enumerate(("#e0703a", "#f2a74b", "#6f6058")):
        out.append(f'<circle cx="{32 + i*18}" cy="28" r="5" fill="{col}"/>')
    out.append(f'<text x="{w/2}" y="32" text-anchor="middle" class="mono" style="font-size:11px">~/{esc(c["username"])} — about.md</text>')
    y = 86
    out.append(f'<g class="fade"><text x="34" y="{y}" class="prompt">❯</text><text x="54" y="{y}" class="cmd">cat about.md</text></g>')
    y += 32
    for i, line in enumerate(lines):
        if line:
            out.append(f'<text x="54" y="{y}" class="out rise" style="animation-delay:{.15 + i*.08:.2f}s">{esc(line)}</text>')
        y += 22
    y += 14
    out.append(f'<g class="fade" style="animation-delay:.9s"><text x="34" y="{y}" class="prompt">❯</text>'
               f'<text x="54" y="{y}" class="cmd">echo $FOCUS</text>'
               f'<text x="190" y="{y}" class="key">web apps for small businesses in Morocco</text>'
               f'<rect x="508" y="{y-12}" width="8" height="15" fill="{COPPER}" class="cursor"/></g>')
    out.append('</svg>')
    return "".join(out)


# ── project cards ────────────────────────────────────────────────────────────
def project(i: int, p: dict) -> str:
    w, h = 440, 236
    live = p["status"] == "LIVE"
    css = f""".idx{{font:600 11px {MONO};fill:{DIM};letter-spacing:1.5px}}.title{{font:700 26px {SANS};fill:{SAND};letter-spacing:-.6px}}
.kind{{font:600 13px {SANS};fill:{COPPER}}}.desc{{font:12.5px {SANS};fill:{MUTED}}}.st{{font:700 9px {MONO};letter-spacing:1.4px}}
.cta{{font:600 10px {MONO};fill:{AMBER};letter-spacing:1.6px}}
@keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}.pulse{{animation:pulse 2.4s ease-in-out infinite}}"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(p["name"])}: {esc(p["kind"])}">',
           defs(css), frame(w, h)]
    out.append(f'<path d="{star(w-44, 44, 20)}" fill="none" stroke="{HAIR}" stroke-width="1.2"/>')
    out.append(f'<text x="28" y="40" class="idx">{i:02d} / PROJECT</text>')
    st_w = len(p["status"]) * 7 + 30
    dot = "#5fd38d" if live else AMBER
    out.append(f'<g transform="translate(28 54)"><rect width="{st_w}" height="20" rx="10" fill="#1c1512" stroke="{HAIR}"/>'
               f'<circle cx="12" cy="10" r="3.5" fill="{dot}" class="pulse"/><text x="22" y="13.5" class="st" fill="{dot}">{esc(p["status"])}</text></g>')
    out.append('<g class="rise">')
    out.append(f'<text x="28" y="112" class="title">{esc(p["name"])}</text>')
    out.append(f'<text x="28" y="134" class="kind">{esc(p["kind"])}</text>')
    for j, line in enumerate(p["lines"]):
        out.append(f'<text x="28" y="{158 + j*17}" class="desc">{esc(line)}</text>')
    out.append('</g>')
    x = 28.0
    for s in p["stack"]:
        svg, cw = chip(x, 192, s)
        out.append(svg)
        x += cw + 6
    out.append('</svg>')
    return "".join(out)


# ── technical expertise ──────────────────────────────────────────────────────
def expertise() -> str:
    groups = CONFIG["expertise"]
    w = 900
    col_w = (w - 80 - 3 * 16) / 4
    rows = max(len(g["items"]) for g in groups)
    h = 84 + 58 + (rows - 1) * 30 + 52
    css = f".item{{font:13px {SANS};fill:#ddd0c3}}.gt{{font:600 10px {MONO};fill:{AMBER};letter-spacing:2px}}"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Technical expertise">',
           defs(css), frame(w, h)]
    out.append(header(40, 40, "FROM THE DATABASE TO THE UI", 300))
    for gi, g in enumerate(groups):
        x = 40 + gi * (col_w + 16)
        top = 84
        out.append(f'<g class="rise" style="animation-delay:{gi*.1:.1f}s">')
        out.append(f'<rect x="{x:.1f}" y="{top}" width="{col_w:.1f}" height="{h-top-28}" rx="14" fill="{PANEL}" stroke="{HAIR_SOFT}"/>')
        out.append(f'<path d="M{x+16:.1f} {top}h40" stroke="{COPPER}" stroke-width="2"/>')
        out.append(f'<text x="{x+16:.1f}" y="{top+28}" class="gt">{esc(g["title"])}</text>')
        for ii, item in enumerate(g["items"]):
            yy = top + 58 + ii * 30
            out.append(f'<path d="{star(x+21, yy-4, 3.6)}" fill="{COPPER}" opacity=".85"/>')
            out.append(f'<text x="{x+34:.1f}" y="{yy}" class="item">{esc(item)}</text>')
        out.append('</g>')
    out.append('</svg>')
    return "".join(out)


# ── activity (real contribution calendar) ────────────────────────────────────
def token() -> str:
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def contributions(username: str) -> list[tuple[dt.date, int]]:
    query = ('query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{'
             'weeks{contributionDays{date contributionCount}}}}}}')
    body = json.dumps({"query": query, "variables": {"u": username}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {token()}", "Content-Type": "application/json", "User-Agent": "profile-generator"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for wk in weeks for d in wk["contributionDays"]]


def streaks(days: list[tuple[dt.date, int]]) -> tuple[int, int]:
    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    seq = list(days)
    if seq and seq[-1][1] == 0:  # today may not have activity yet
        seq = seq[:-1]
    for _, n in reversed(seq):
        if not n:
            break
        current += 1
    return current, longest


def activity() -> str:
    days = contributions(CONFIG["username"])
    total = sum(n for _, n in days)
    active = sum(1 for _, n in days if n)
    current, longest = streaks(days)
    best_day, best_n = max(days, key=lambda d: d[1])
    w, h = 900, 330
    cell, gap = 12, 3
    weeks: list[list[tuple[dt.date, int]]] = []
    for d, n in days:
        if not weeks or d.weekday() == 6:  # GitHub weeks start on Sunday
            weeks.append([])
        weeks[-1].append((d, n))
    weeks = weeks[-53:]
    grid_w = len(weeks) * (cell + gap) - gap
    gx = (w - grid_w) / 2
    gy = 168
    peak = max(1, max(n for _, n in days))

    def shade(n: int) -> str:
        if n == 0:
            return "#1b1512"
        r = n / peak
        if r < .15:
            return "#4a2618"
        if r < .35:
            return "#8a3e1f"
        if r < .65:
            return COPPER
        return AMBER

    css = f""".metric{{font:700 30px {SANS};fill:{SAND};letter-spacing:-.8px}}.ml{{font:600 9px {MONO};fill:{MUTED};letter-spacing:1.6px}}
.mon{{font:10px {MONO};fill:{DIM}}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}.col{{animation:pop .5s {EASE} both}}"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
           f'aria-label="{total} GitHub contributions in the last year across {active} active days">',
           defs(css), frame(w, h)]
    out.append(header(40, 40, f"@{CONFIG['username'].upper()}  /  LAST 12 MONTHS", 340))
    metrics = [(f"{total:,}", "CONTRIBUTIONS"), (str(active), "ACTIVE DAYS"),
               (f"{longest}d", "LONGEST STREAK"), (f"{current}d", "CURRENT STREAK")]
    mw = (w - 80 - 3 * 14) / 4
    for i, (v, l) in enumerate(metrics):
        x = 40 + i * (mw + 14)
        out.append(f'<g class="rise" style="animation-delay:{i*.08:.2f}s"><rect x="{x:.1f}" y="78" width="{mw:.1f}" height="66" rx="13" fill="{PANEL}" stroke="{HAIR_SOFT}"/>'
                   f'<text x="{x+18:.1f}" y="114" class="metric">{v}</text><text x="{x+18:.1f}" y="132" class="ml">{l}</text></g>')
    last_month = None
    for wi, wk in enumerate(weeks):
        x = gx + wi * (cell + gap)
        m = wk[0][0].month
        if m != last_month and wk[0][0].day <= 7:
            out.append(f'<text x="{x:.1f}" y="{gy-6}" class="mon">{wk[0][0].strftime("%b")}</text>')
        last_month = m
        out.append(f'<g class="col" style="animation-delay:{wi*0.012:.3f}s">')
        for d, n in wk:
            y = gy + 4 + ((d.weekday() + 1) % 7) * (cell + gap)
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{shade(n)}"/>')
        out.append('</g>')
    fy = h - 30
    out.append(f'<text x="40" y="{fy}" class="ml">BUSIEST DAY  {best_day.strftime("%d %b %Y").upper()}  ·  {best_n} CONTRIBUTIONS</text>')
    lx = w - 40 - 5 * 15 - 70
    out.append(f'<text x="{lx-8}" y="{fy}" text-anchor="end" class="ml">LESS</text>')
    for i, col in enumerate(["#1b1512", "#4a2618", "#8a3e1f", COPPER, AMBER]):
        out.append(f'<rect x="{lx + i*15}" y="{fy-10}" width="11" height="11" rx="2.5" fill="{col}"/>')
    out.append(f'<text x="{lx + 5*15 + 4}" y="{fy}" class="ml">MORE</text>')
    out.append(f'<text x="{w-40}" y="{h-14}" text-anchor="end" class="mon" style="font-size:9px">updated {dt.date.today().isoformat()} · includes private contributions GitHub shows publicly</text>')
    out.append('</svg>')
    return "".join(out)


if __name__ == "__main__":
    write("hero.svg", hero())
    write("about.svg", about())
    for i, p in enumerate(CONFIG["projects"], 1):
        write(f"project-{p['slug']}.svg", project(i, p))
    write("expertise.svg", expertise())
    write("activity.svg", activity())
