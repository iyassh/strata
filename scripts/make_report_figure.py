"""Draw the report-level STRATA framework figure as a tiered block diagram.

Writes paper/figures/strata_framework_report.svg; convert with rsvg-convert.
"""
from pathlib import Path

W, H = 1500, 1064
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
W = 1700
BLUE = "#2B5C8C"
ORANGE = "#B8651F"
LEFT = 118            # left margin for the bracket labels
RIGHT_PILLAR = 96
CHANNEL = 84          # gap between the stack and the pillar; carries the signature-event bypass
STACK_W = W - LEFT - RIGHT_PILLAR - CHANNEL - 16
HDR_H = 54
GAP = 14
TIER_GAP = 50         # room between tiers for the one labelled arrow
DEPTH = 6

def header(tier, y, label, sub, stage=None):
    block(LEFT, y, STACK_W, HDR_H, tier["hdr"], tier["edge"], rx=8, depth=DEPTH)
    x = LEFT + 22
    if stage:
        pw = 34 if len(stage) <= 2 else 20 + 11 * len(stage)
        rect(x, y + 10, pw, 34, "white", rx=17)
        text(x + pw / 2, y + 33, stage, size=16, weight="bold", fill=tier["hdr"], anchor="middle")
        x += pw + 14
    text(x, y + 36, label, size=25, weight="bold", fill="white")
    text(LEFT + STACK_W - 22, y + 35, sub, size=20, fill="#EEF2F6", anchor="end")

def tile(tier, x, y, w, h, it):
    block(x, y, w, h, tier["tile"], tier["edge"], rx=10, depth=DEPTH)
    tx = x + 18
    if it.get("icon"):
        icon(it["icon"], x + 18, y + 22, tier["hdr"])
        tx = x + 78
    if it.get("badge"):
        badge(x + w - 26, y + 26, it["badge"], tier["hdr"])
    text(tx, y + 36, it["title"], size=22, weight="bold", fill=tier["txt"])
    wrap(tx, y + 64, it.get("lines", []), size=18, dy=22, fill="#333")
    return (x, y, w, h)

def row(tier, y, items, h, gap=GAP):
    n = len(items)
    w = (STACK_W - gap * (n - 1)) / n
    pos = []
    for i, it in enumerate(items):
        pos.append(tile(tier, LEFT + i * (w + gap), y, w, h, it))
    return pos

def varrow(x, y0, y1, color, marker, dashed=False, label=None, label_side="right", halo=True, label_y=None):
    dash = ' stroke-dasharray="9 7"' if dashed else ''
    if halo:
        out.append(f'<path d="M{x} {y0} V{y1}" stroke="white" stroke-width="9" fill="none" stroke-linecap="round"/>')
    out.append(f'<path d="M{x} {y0} V{y1}" stroke="{color}" stroke-width="3"{dash} fill="none" marker-end="url(#{marker})"/>')
    if label:
        ym = label_y if label_y is not None else (y0 + y1) / 2 + 6
        if label_side == "right":
            text(x + 14, ym, label, size=17, fill=color, anchor="start", extra='font-style="italic"')
        else:
            text(x - 14, ym, label, size=17, fill=color, anchor="end", extra='font-style="italic"')

# ---------------------------------------------------------------- tiers
T = {t["key"]: t for t in TIERS}
y = 24

# Tier 1: SENSE
sense_top = y
header(T["sense"], y, "SENSE", "the building's own data, turned into events", stage="1–2")
y += HDR_H + GAP
r1 = row(T["sense"], y, [
    dict(badge="1", icon="sensor", title="Trend data", lines=[
        "What the building-automation system already records:",
        "temperatures, flows, damper and valve positions, fan",
        "speeds, once a minute. No new sensors."]),
    dict(badge="1", icon="file", title="Configuration file", lines=[
        "Maps sensor names to roles and lists the control sequence",
        "as rules. The only building-specific part: a new building",
        "means a new file, not code."]),
], 124)
y += 124 + GAP + 2
# Events: one full-width tile with the two chips side by side
EV_H = 92
ex, ey, ew, eh = tile(T["sense"], LEFT, y, STACK_W, EV_H, dict(title="Events"))
badge(LEFT + 112, y + 29, "2", T["sense"]["hdr"])
text(LEFT + 18, y + 62, "one case per day,", size=16, fill="#333")
text(LEFT + 18, y + 81, "rebuilt every new day", size=16, fill="#333")
CHIP_W = 520
chip1_x = LEFT + 230
chip2_x = chip1_x + CHIP_W + 40
chip_y = y + 28
for cx_, label, stroke, fill in [(chip1_x, "State events: what the equipment is doing", BLUE, "#FFFFFF"),
                                 (chip2_x, "Signature events: what should not happen", ORANGE, "#FFF4EA")]:
    rect(cx_, chip_y, CHIP_W, 36, fill, stroke=stroke, rx=8, sw=2.5)
    text(cx_ + 16, chip_y + 25, label, size=18, weight="bold", fill=stroke)
state_cx = chip1_x + 120
sig_mid_y = chip_y + 18
y += EV_H
sense_bottom = y + DEPTH
y += TIER_GAP

# Tier 2: UNDERSTAND
understand_top = y
header(T["understand"], y, "UNDERSTAND", "what a normal day looks like, learned from one fault-free period", stage="3–4a")
y += HDR_H + GAP
r2 = row(T["understand"], y, [
    dict(badge="3", icon="model", title="Process models", lines=[
        "Discovered from the state events only, so",
        "they cannot learn the configured fault rules.",
        "One per terminal unit; one for the whole unit."]),
    dict(badge="4a", icon="gauge", title="Calibration", lines=[
        "Healthy bands and model thresholds for",
        "every check come from the fault-free days.",
        "No threshold ever sees fault data."]),
    dict(badge="4a", icon="calendar", title="Held-out days", lines=[
        "The last eight days of each month (96 a",
        "year) are kept aside and used only to",
        "measure each check's false-alarm rate."]),
], 130)
y += 130
understand_bottom = y + DEPTH
y += TIER_GAP

# Tier 3: CHECK
check_top = y
header(T["check"], y, "CHECK", "eight checks score every new day, each against its own threshold", stage="4b")
y += HDR_H + GAP
checks = [
    ("Unit\nconformance", ["day fits the", "unit model"]),
    ("Terminal-unit\nconformance", ["day fits the", "terminal-unit", "model"]),
    ("Absence", ["expected", "terminal unit", "silent"]),
    ("Frequency", ["daily count", "out of", "range"]),
    ("Rate", ["last 30 days", "against same", "month;", "support only"]),
    ("Oscillation", ["actuator", "reversing", "too often"]),
    ("Residual", ["physical", "relationship", "drifted"]),
    ("Rules", ["a control", "rule broken:", "a signature", "event"]),
]
n = len(checks); cgap = 12; cw = (STACK_W - cgap * (n - 1)) / n
CH_H = 156
ty = y
cpos = []
for i, (name, lines) in enumerate(checks):
    x = LEFT + i * (cw + cgap)
    block(x, ty, cw, CH_H, T["check"]["tile"], T["check"]["edge"], rx=10, depth=DEPTH)
    cpos.append((x, ty, cw, CH_H))
    parts = name.split("\n")
    for j, part in enumerate(parts):
        text(x + 14, ty + 30 + 22 * j, part, size=19, weight="bold", fill=T["check"]["txt"])
    wrap(x + 14, ty + 58 + 22 * (len(parts) - 1) + 2, lines, size=20, dy=23, fill="#333")
gy = ty + CH_H + 24
x0 = LEFT; x1 = LEFT + 5 * cw + 4 * cgap
out.append(f'<path d="M{x0+4} {gy} h{x1-x0-8}" stroke="{T["check"]["hdr"]}" stroke-width="2.5" fill="none"/>')
text((x0 + x1) / 2, gy + 22, "read the event log", size=17, fill=T["check"]["txt"], anchor="middle", extra='font-style="italic"')
x0 = LEFT + 5 * (cw + cgap); x1 = LEFT + 8 * cw + 7 * cgap
out.append(f'<path d="M{x0+4} {gy} h{x1-x0-8}" stroke="{T["check"]["hdr"]}" stroke-width="2.5" fill="none"/>')
text((x0 + x1) / 2, gy + 22, "read the raw sensors", size=17, fill=T["check"]["txt"], anchor="middle", extra='font-style="italic"')
check_bottom = gy + 30
y = check_bottom + TIER_GAP

# Tier 4: ALERT
alert_top = y
header(T["alert"], y, "ALERT", "only what beats its own false-alarm rate reaches the operator", stage="5–6")
y += HDR_H + GAP
r4 = row(T["alert"], y, [
    dict(badge="5", icon="gate", title="Noise gate", lines=[
        "A check may alarm only when its flags exceed what",
        "its own false-alarm rate would produce by chance.",
        "The rate is never taken below 3 days in 96."]),
    dict(badge="6", icon="bell", title="Alarm to the operator", lines=[
        "What broke.  Where: unit, terminal unit, zone.",
        "The evidence: values and duration.",
        "The check's measured false-alarm rate."]),
], 130)
y += 130 + DEPTH + 10
BOTTOM = y
H = BOTTOM + 14

# ---------------------------------------------------------------- flow arrows (tile to tile)
pm = r2[0]                                   # Process models tile
# 1. state events -> process models (crosses the UNDERSTAND header)
varrow(state_cx, sense_bottom + 2, pm[1] - 3, BLUE, "ab",
       label="state events only", label_side="right", label_y=sense_bottom + 30)
# 5. signature events -> Rules check: down out of the chip, across the gap, down the channel, into Rules
rules = cpos[-1]
cx = LEFT + STACK_W + DEPTH + CHANNEL - 16
rules_mid = rules[1] + rules[3] / 2
sx = chip2_x + CHIP_W - 60
gap_y = sense_bottom + 24
out.append(f'<path d="M{sx} {chip_y + 36} V{gap_y} H{cx} V{rules_mid} H{rules[0] + rules[2] + DEPTH + 4}" '
           f'stroke="{ORANGE}" stroke-width="3" stroke-dasharray="9 7" fill="none" marker-end="url(#ao)"/>')
text(sx - 14, gap_y + 6, "signature events skip the models and go only to the Rules check", size=17, fill=ORANGE,
     anchor="end", extra='font-style="italic"')

# ---------------------------------------------------------------- side pillar
px = LEFT + STACK_W + DEPTH + CHANNEL
block(px, 24, RIGHT_PILLAR, BOTTOM - 24, "#1E3550", "#121F30", rx=8, depth=DEPTH)
text(px + RIGHT_PILLAR / 2 + 8, (BOTTOM + 24) / 2, "STRATA", size=40, weight="bold", fill="white", anchor="middle",
     extra=f'transform="rotate(-90 {px + RIGHT_PILLAR/2 + 10} {(BOTTOM + 24)/2})" letter-spacing="6"')
text(px + RIGHT_PILLAR / 2 + 38, (BOTTOM + 24) / 2, "a process-mining framework for HVAC fault detection", size=16, fill="#C9D3E0", anchor="middle",
     extra=f'transform="rotate(-90 {px + RIGHT_PILLAR/2 + 44} {(BOTTOM + 24)/2})"')

# ---------------------------------------------------------------- left brackets
def bracket(y0, y1, label):
    bx = LEFT - 26
    out.append(f'<path d="M{bx} {y0} h-10 v{y1-y0} h10" stroke="#555" stroke-width="2" fill="none"/>')
    cy = (y0 + y1) / 2
    text(bx - 30, cy, label, size=18, weight="bold", fill="#444", anchor="middle", extra=f'transform="rotate(-90 {bx-30} {cy})"')

bracket(sense_top, understand_bottom, "built once per building")
bracket(check_top, BOTTOM, "run on every new day")

out.append('</svg>')
out.insert(0, f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
              f'<rect width="{W}" height="{H}" fill="white"/>'
              f'<defs>'
              f'<marker id="ab" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
              f'<path d="M0 0 L10 5 L0 10 z" fill="{BLUE}"/></marker>'
              f'<marker id="ao" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
              f'<path d="M0 0 L10 5 L0 10 z" fill="{ORANGE}"/></marker>'
              f'</defs>')
Path("paper/figures/strata_framework_report.svg").write_text("\n".join(out))
print("wrote svg", W, H)
