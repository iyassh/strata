"""Draw the report-level STRATA framework figure as a tiered block diagram.

Writes paper/figures/strata_framework_report.svg; convert with rsvg-convert.
"""
from pathlib import Path

W, H = 1500, 1040
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
out = []

TIERS = [
    dict(key="sense", hdr="#2B5C8C", tile="#E3EDF7", edge="#1F4466", txt="#17324D"),
    dict(key="understand", hdr="#3C7A4C", tile="#E2F0E4", edge="#2B5A37", txt="#1C3B23"),
    dict(key="check", hdr="#B8651F", tile="#FBEBDC", edge="#8A4A14", txt="#4A2A0E"),
    dict(key="alert", hdr="#1E3550", tile="#E0E5EC", edge="#121F30", txt="#121F30"),
]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")

def rect(x, y, w, h, fill, stroke="none", rx=10, sw=0, extra=""):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

def block(x, y, w, h, fill, edge, rx=10, depth=7):
    # extruded block: dark edge offset down-right, then face
    rect(x + depth, y + depth, w, h, edge, rx=rx)
    rect(x, y, w, h, fill, rx=rx)

def text(x, y, s, size=18, weight="normal", fill="#222", anchor="start", extra=""):
    out.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')

def wrap(x, y, lines, size=17, dy=21, fill="#333", anchor="start"):
    for i, s in enumerate(lines):
        text(x, y + i * dy, s, size=size, fill=fill, anchor=anchor)

def badge(x, y, label, fill):
    out.append(f'<circle cx="{x}" cy="{y}" r="17" fill="{fill}"/>')
    text(x, y + 6, label, size=17, weight="bold", fill="white", anchor="middle")

# --- icons (simple glyphs, stroke-based) ---
def icon(kind, x, y, color):
    s = f'stroke="{color}" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "sensor":
        out.append(f'<circle cx="{x+20}" cy="{y+26}" r="6" fill="{color}"/>')
        out.append(f'<path d="M{x+8} {y+14} a17 17 0 0 1 24 0 M{x+1} {y+7} a27 27 0 0 1 38 0" {s}/>')
        out.append(f'<path d="M{x+20} {y+32} v12" {s}/>')
    elif kind == "file":
        out.append(f'<path d="M{x+6} {y+2} h20 l10 10 v30 h-30 z M{x+26} {y+2} v10 h10" {s}/>')
        out.append(f'<path d="M{x+12} {y+22} h18 M{x+12} {y+30} h18 M{x+12} {y+38} h10" {s}/>')
    elif kind == "events":
        for i, yy in enumerate((8, 22, 36)):
            out.append(f'<circle cx="{x+8}" cy="{y+yy}" r="4" fill="{color}"/>')
            out.append(f'<path d="M{x+18} {y+yy} h{24 - 6*i}" {s}/>')
        out.append(f'<path d="M{x+8} {y+8} v28" stroke="{color}" stroke-width="2" fill="none"/>')
    elif kind == "model":
        pts = [(x+6, y+22), (x+22, y+6), (x+22, y+38), (x+40, y+22)]
        out.append(f'<path d="M{pts[0][0]} {pts[0][1]} L{pts[1][0]} {pts[1][1]} L{pts[3][0]} {pts[3][1]} L{pts[2][0]} {pts[2][1]} Z M{pts[0][0]} {pts[0][1]} L{pts[3][0]} {pts[3][1]}" {s}/>')
        for px, py in pts:
            out.append(f'<circle cx="{px}" cy="{py}" r="5" fill="{color}"/>')
    elif kind == "gauge":
        out.append(f'<path d="M{x+4} {y+34} a20 20 0 0 1 40 0" {s}/>')
        out.append(f'<path d="M{x+24} {y+34} l10 -16" {s}/>')
        out.append(f'<circle cx="{x+24}" cy="{y+34}" r="4" fill="{color}"/>')
    elif kind == "calendar":
        out.append(f'<rect x="{x+4}" y="{y+8}" width="38" height="34" rx="4" {s}/>')
        out.append(f'<path d="M{x+4} {y+18} h38 M{x+14} {y+4} v8 M{x+32} {y+4} v8" {s}/>')
        out.append(f'<rect x="{x+26}" y="{y+24}" width="12" height="12" fill="{color}"/>')
    elif kind == "gate":
        out.append(f'<path d="M{x+4} {y+6} h40 l-15 18 v16 l-10 5 v-21 z" {s}/>')
    elif kind == "bell":
        out.append(f'<path d="M{x+10} {y+32} v-12 a13 13 0 0 1 26 0 v12 l4 5 h-34 z" {s}/>')
        out.append(f'<path d="M{x+18} {y+41} a5 5 0 0 0 10 0" {s}/>')

# ---------------------------------------------------------------- canvas
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append(f'<rect width="{W}" height="{H}" fill="white"/>')

LEFT = 118            # left margin for the bracket labels
RIGHT_PILLAR = 96
STACK_W = W - LEFT - RIGHT_PILLAR - 46
HDR_H = 54
GAP = 14
y = 24

def header(tier, y, label, sub, stage=None):
    block(LEFT, y, STACK_W, HDR_H, tier["hdr"], tier["edge"], rx=8, depth=6)
    x = LEFT + 22
    if stage:
        pw = 34 if len(stage) <= 2 else 20 + 11 * len(stage)
        rect(x, y + 10, pw, 34, "white", rx=17)
        text(x + pw / 2, y + 33, stage, size=16, weight="bold", fill=tier["hdr"], anchor="middle")
        x += pw + 14
    out.append(f'<text x="{x}" y="{y+36}" font-family="{FONT}" fill="white"><tspan font-size="25" font-weight="bold">{esc(label)}</tspan><tspan dx="18" font-size="20" fill="#EEF2F6">{esc(sub)}</tspan></text>')

def tiles(tier, y, items, h, ncols=None):
    n = len(items)
    gap = 14
    w = (STACK_W - gap * (n - 1)) / n
    for i, it in enumerate(items):
        x = LEFT + i * (w + gap)
        block(x, y, w, h, tier["tile"], tier["edge"], rx=10, depth=6)
        tx = x + 18
        if it.get("icon"):
            icon(it["icon"], x + 18, y + 22, tier["hdr"])
            tx = x + 78
        if it.get("badge"):
            badge(x + w - 26, y + 26, it["badge"], tier["hdr"])
        text(tx, y + 36, it["title"], size=22, weight="bold", fill=tier["txt"])
        wrap(tx, y + 64, it.get("lines", []), size=18, dy=22, fill="#333")
    return y + h

# ---------------------------------------------------------------- tiers
T = {t["key"]: t for t in TIERS}

# Tier 1: SENSE
header(T["sense"], y, "SENSE", "the building's own data, turned into events", stage="1–2")
y += HDR_H + GAP
y = tiles(T["sense"], y, [
    dict(badge="1", icon="sensor", title="Trend data", lines=[
        "What the building-automation",
        "system already records: temperatures,",
        "flows, damper and valve positions,",
        "fan speeds, once a minute."]),
    dict(badge="1", icon="file", title="Configuration file", lines=[
        "Maps sensor names to roles and lists",
        "the control sequence as rules. The",
        "only building-specific part: a new",
        "building means a new file, not code."]),
    dict(badge="2", icon="events", title="Events", lines=[
        "Each day is one case. State events:",
        "what the equipment is doing.",
        "Signature events: what should not",
        "happen. The two are kept apart."]),
], 152)
y += GAP + 8

# Tier 2: UNDERSTAND
header(T["understand"], y, "UNDERSTAND", "what a normal day looks like, learned from one fault-free period", stage="3–4a")
y += HDR_H + GAP
y = tiles(T["understand"], y, [
    dict(badge="3", icon="model", title="Process models", lines=[
        "Discovered from the state events",
        "only, so they cannot learn our own",
        "fault rules. One per terminal unit;",
        "one for the whole unit."]),
    dict(badge="4a", icon="gauge", title="Calibration", lines=[
        "Healthy bands and model thresholds",
        "for every check come from the",
        "fault-free days. No threshold ever",
        "sees fault data."]),
    dict(badge="4a", icon="calendar", title="Held-out days", lines=[
        "The last eight days of each month",
        "(96 a year) are kept aside and used",
        "only to measure each check's",
        "false-alarm rate."]),
], 152)
y += GAP + 8

# Tier 3: CHECK
header(T["check"], y, "CHECK", "eight checks score every new day against its own healthy band", stage="4b")
y += HDR_H + GAP
checks = [
    ("Rules", ["control-", "sequence", "rule broken"]),
    ("Residual", ["physical", "relation", "drifted"]),
    ("Oscillation", ["actuator", "reversing", "too often"]),
    ("Unit\nconformance", ["day fits the", "unit model"]),
    ("Device\nconformance", ["day fits the", "terminal-unit", "model"]),
    ("Absence", ["expected", "device", "silent"]),
    ("Frequency", ["daily count", "out of", "range"]),
    ("Rate", ["30-day activity", "vs same month;", "support only"]),
]
n = len(checks); gap = 12; w = (STACK_W - gap * (n - 1)) / n
ty = y
for i, (name, lines) in enumerate(checks):
    x = LEFT + i * (w + gap)
    block(x, ty, w, 132, T["check"]["tile"], T["check"]["edge"], rx=10, depth=6)
    parts = name.split("\n")
    for j, part in enumerate(parts):
        text(x + 14, ty + 30 + 22 * j, part, size=19, weight="bold", fill=T["check"]["txt"])
    wrap(x + 14, ty + 56 + 22 * (len(parts) - 1) + 2, lines, size=17, dy=20, fill="#333")
# group labels under the tiles
gy = ty + 132 + 24
x0 = LEFT; x1 = LEFT + 3 * w + 2 * gap
out.append(f'<path d="M{x0+4} {gy} h{x1-x0-8}" stroke="{T["check"]["hdr"]}" stroke-width="2.5" fill="none"/>')
text((x0 + x1) / 2, gy + 22, "read the raw sensors", size=17, fill=T["check"]["txt"], anchor="middle", extra='font-style="italic"')
x0 = LEFT + 3 * (w + gap); x1 = LEFT + 7 * w + 6 * gap
out.append(f'<path d="M{x0+4} {gy} h{x1-x0-8}" stroke="{T["check"]["hdr"]}" stroke-width="2.5" fill="none"/>')
text((x0 + x1) / 2, gy + 22, "read the event log", size=17, fill=T["check"]["txt"], anchor="middle", extra='font-style="italic"')
y = gy + 36 + GAP

# Tier 4: ALERT
header(T["alert"], y, "ALERT", "only what beats its own false-alarm rate reaches the operator", stage="5–6")
y += HDR_H + GAP
y = tiles(T["alert"], y, [
    dict(badge="5", icon="gate", title="Noise gate", lines=[
        "A check may alarm only when its flags exceed",
        "what its own false-alarm rate would produce",
        "by chance. The rate is never taken below",
        "3 days in 96."]),
    dict(badge="6", icon="bell", title="Alarm to the operator", lines=[
        "What broke.  Where: unit, terminal unit, zone.",
        "The evidence: values and duration.",
        "The check's measured false-alarm rate."]),
], 152)
y += 10
BOTTOM = y

# ---------------------------------------------------------------- side pillar
px = LEFT + STACK_W + 30
block(px, 24, RIGHT_PILLAR, BOTTOM - 24, "#1E3550", "#121F30", rx=8, depth=6)
text(px + RIGHT_PILLAR / 2 + 8, (BOTTOM + 24) / 2, "STRATA", size=40, weight="bold", fill="white", anchor="middle",
     extra=f'transform="rotate(-90 {px + RIGHT_PILLAR/2 + 10} {(BOTTOM + 24)/2})" letter-spacing="6"')
text(px + RIGHT_PILLAR / 2 + 38, (BOTTOM + 24) / 2, "a process-mining framework for HVAC fault detection", size=16, fill="#C9D3E0", anchor="middle",
     extra=f'transform="rotate(-90 {px + RIGHT_PILLAR/2 + 44} {(BOTTOM + 24)/2})"')

# ---------------------------------------------------------------- left brackets
def bracket(y0, y1, label):
    bx = LEFT - 26
    out.append(f'<path d="M{bx} {y0} h-10 v{y1-y0} h10" stroke="#555" stroke-width="2" fill="none"/>')
    cy = (y0 + y1) / 2
    text(bx - 30, cy, label, size=19, weight="bold", fill="#444", anchor="middle", extra=f'transform="rotate(-90 {bx-30} {cy})"')

# tiers 1-2 once, 3-4 daily: compute from positions (approximate by known layout)
t1_top = 24; t2_bottom = 24 + (HDR_H + GAP + 152 + GAP + 8) * 2 - GAP - 8 + 6
bracket(t1_top, t2_bottom, "set up once per building")
bracket(t2_bottom + GAP + 8, BOTTOM, "runs every day")
text(LEFT - 56, t2_bottom + 2, "", size=10)

out.append('</svg>')
Path("paper/figures/strata_framework_report.svg").write_text("\n".join(out))
print("wrote svg", W, H)
