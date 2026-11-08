"""Back-silkscreen art generator for the Leyden Jar V2 controller (work in progress, preview only).

Usage:  python -I backsilk.py [board.kicad_pcb] [out.svg]
Preview PNG (headless Edge):
  msedge --headless=new --disable-gpu --hide-scrollbars --window-size=1914,612 --screenshot=out.png file:///<abs path>/out.svg
Not yet done: J4, RUN/BOOT labels, board identity (title, logo), conversion to a footprint (text to outlines).

Reads the board geometry (read-only) and renders the bottom view with the art layer.
All art is defined in VIEW coordinates: millimetres, as seen from the bottom of the board
(board x mirrored: vx = XM - x, vy = y), so text reads normally.
"""
import math, re, sys, html

import os
HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "Leyden_Jar.kicad_pcb")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "backsilk_preview.svg")
CROP = (-1.0, -0.6, 86.0, 27.2)
XM = 84.5                                 # mirror axis: vx = XM - x
CLEAR = 0.15                              # silk to exposed copper (mm)

MASK, SILK, CU, HOLE, VIA = "#1d3a2c", "#f2f2ee", "#c9cdd1", "#0b140f", "#2f5442"
FONT = "Bahnschrift, 'Liberation Sans Narrow', 'Arial Narrow', sans-serif"
CHAR_W = 0.62                             # estimated advance / height, condensed semibold

def VX(x):
    return XM - x

# ---------------------------------------------------------------- board geometry
src = open(BOARD, encoding="utf-8").read()

def block(s, st):
    d = 0
    for j in range(st, len(s)):
        if s[j] == "(":
            d += 1
        elif s[j] == ")":
            d -= 1
            if d == 0:
                return s[st:j + 1]

def nums(t):
    return [float(v) for v in t.split()]

pads = []      # dict(kind, shape, x, y, w, h, ang, drill, ref, num)  view coords
for m in re.finditer(r"\n\t\(footprint \"", src):
    fb = block(src, m.start() + 2)
    ref = re.search(r'\(property "Reference" "([^"]+)"', fb).group(1)
    at = nums(re.search(r"\n\t\t\(at ([^)]+)\)", fb).group(1))
    X, Y, rot = at[0], at[1], (at[2] if len(at) > 2 else 0.0)
    t = math.radians(rot)
    for pm in re.finditer(r"\n\t\t\(pad \"([^\"]*)\" (\w+) (\w+)", fb):
        pb = block(fb, pm.start() + 3)
        num, kind, shape = pm.groups()
        pat = nums(re.search(r"\(at ([^)]+)\)", pb).group(1))
        px, py = pat[0], pat[1]
        pang = pat[2] if len(pat) > 2 else 0.0
        w, h = nums(re.search(r"\(size ([^)]+)\)", pb).group(1))
        layers = re.search(r"\(layers ([^)]*)\)", pb).group(1)
        dr = re.search(r"\(drill (?:oval )?([\d.]+)", pb)
        bx = X + px * math.cos(t) + py * math.sin(t)
        by = Y - px * math.sin(t) + py * math.cos(t)
        back = kind in ("thru_hole", "np_thru_hole") or "B.Cu" in layers
        if not back:
            continue
        pads.append(dict(kind=kind, shape=shape, x=VX(bx), y=by, w=w, h=h, ang=-pang,
                         drill=float(dr.group(1)) if dr else 0.0, ref=ref, num=num))

J9_SHIFT = float(__import__("os").environ.get("J9_SHIFT", "0"))   # what-if: move J9 up (mm)
for p_ in pads:
    if p_["ref"] == "J9":
        p_["y"] -= J9_SHIFT

vias = []
for m in re.finditer(r"\(via\s*\(at ([^)]+)\)\s*\(size ([^)]+)\)", src):
    x, y = nums(m.group(1))[:2]
    vias.append((VX(x), y, float(m.group(2)) / 2))

edges = []     # polylines in view coords
for m in re.finditer(r"\n\t\(gr_(line|arc)", src):
    b = block(src, m.start() + 2)
    if '"Edge.Cuts"' not in b:
        continue
    st = nums(re.search(r"\(start ([^)]+)\)", b).group(1))
    en = nums(re.search(r"\(end ([^)]+)\)", b).group(1))
    if m.group(1) == "line":
        edges.append([st, en])
    else:
        mid = nums(re.search(r"\(mid ([^)]+)\)", b).group(1))
        (ax, ay), (bx_, by_), (cx, cy) = st, mid, en
        d = 2 * (ax * (by_ - cy) + bx_ * (cy - ay) + cx * (ay - by_))
        ux = ((ax**2 + ay**2) * (by_ - cy) + (bx_**2 + by_**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by_)) / d
        uy = ((ax**2 + ay**2) * (cx - bx_) + (bx_**2 + by_**2) * (ax - cx) + (cx**2 + cy**2) * (bx_ - ax)) / d
        r = math.hypot(ax - ux, ay - uy)
        a0, a1, am = (math.atan2(p[1] - uy, p[0] - ux) for p in (st, en, mid))
        da = (a1 - a0) % (2 * math.pi)
        if not (0 <= (am - a0) % (2 * math.pi) <= da):
            da -= 2 * math.pi
        edges.append([[ux + r * math.cos(a0 + da * k / 12), uy + r * math.sin(a0 + da * k / 12)] for k in range(13)])
edges = [[(VX(x), y) for x, y in e] for e in edges]

# ---------------------------------------------------------------- art primitives (view coords)
art = []       # (svg, bbox x0,y0,x1,y1, label)

def text(x, y, s, h=0.85, anchor="middle", fill=SILK, weight=600, label=None):
    """(x, y) = anchor point on the text's vertical centre line."""
    w = len(s) * CHAR_W * h
    x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
    svg = (f'<text x="{x:.3f}" y="{y + 0.36 * h:.3f}" font-size="{h * 1.36:.3f}" text-anchor="{anchor}" '
           f'font-family="{FONT}" font-weight="{weight}" font-stretch="condensed" fill="{fill}">{html.escape(s)}</text>')
    art.append((svg, (x0, y - h / 2, x0 + w, y + h / 2), label or s))

def rect(x0, y0, x1, y1, r=0.0, fill=SILK, stroke=None, sw=0.15, label="rect"):
    f = fill if fill else "none"
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    svg = f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{x1 - x0:.3f}" height="{y1 - y0:.3f}" rx="{r}" fill="{f}"{st}/>'
    pad = sw / 2 if stroke else 0
    art.append((svg, (x0 - pad, y0 - pad, x1 + pad, y1 + pad), label))

def path(d, pts, sw=0.15, label="line", fill="none"):
    svg = f'<path d="{d}" fill="{fill}" stroke="{SILK}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    art.append((svg, (min(xs) - sw / 2, min(ys) - sw / 2, max(xs) + sw / 2, max(ys) + sw / 2), label))

def tab(xc, yc, s, h=1.2, th=0.85, padx=0.45, label=None):
    w = len(s) * CHAR_W * th + 2 * padx
    rect(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2, r=0.25, label=label or f"tab {s}")
    text(xc, yc, s, h=th, fill=MASK, label=label or f"tab {s}")

# ---------------------------------------------------------------- stroked shapes (sampled polylines)
strokes = []   # (points, sw, label) for the precise clearance check

def poly(pts, sw=0.15, closed=False, label="line"):
    d = "M" + " L".join(f"{x:.3f} {y:.3f}" for x, y in pts) + (" Z" if closed else "")
    svg = f'<path d="{d}" fill="none" stroke="{SILK}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    art.append((svg, None, label))
    strokes.append((pts + ([pts[0]] if closed else []), sw, label))

def arc_pts(cx, cy, r, a0, a1, n=10):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]

def rrect_pts(x0, y0, x1, y1, r):
    return (arc_pts(x1 - r, y0 + r, r, -90, 0) + arc_pts(x1 - r, y1 - r, r, 0, 90) +
            arc_pts(x0 + r, y1 - r, r, 90, 180) + arc_pts(x0 + r, y0 + r, r, 180, 270))

def circle_pts(cx, cy, r):
    return arc_pts(cx, cy, r, 0, 360, 24)

# ---------------------------------------------------------------- the design
# J7: codes, a bracket per group, white tab hanging from the bracket
J7 = ["3V3", "47", "46", "41", "5V", "GND", "32", "5V", "GND", "45",
      "GND", "3V3", "SCK", "MOSI", "RST", "DC", "CS", "BLK"]
j7x = [VX(11.6 + 2.54 * i) for i in range(18)]
CODE_Y, BR_Y, TICK_Y = 2.83, 3.45, 2.55
for x, s in zip(j7x, J7):
    text(x, CODE_Y, s)

def rounded(pts, r):
    """Polyline with every interior corner rounded (radius r, quadratic fillet)."""
    out = [pts[0]]
    for (ax, ay), (bx, by), (cx, cy) in zip(pts, pts[1:], pts[2:]):
        l1, l2 = math.hypot(bx - ax, by - ay), math.hypot(cx - bx, cy - by)
        k1, k2 = min(r, l1 / 2) / l1, min(r, l2 / 2) / l2
        p0 = (bx + (ax - bx) * k1, by + (ay - by) * k1)
        p2 = (bx + (cx - bx) * k2, by + (cy - by) * k2)
        out += [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * bx + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * by + t * t * p2[1]) for t in (k / 8 for k in range(9))]
    return out + [pts[-1]]

def hang_tab(xc, y, s, h=1.2, th=0.85, padx=0.45, r=0.3, label=None):
    """White tab hanging from a line at y: square top, rounded bottom corners."""
    w = len(s) * CHAR_W * th + 2 * padx
    x0, x1 = xc - w / 2, xc + w / 2
    art.append((f'<path d="M{x0:.3f} {y:.3f} H{x1:.3f} V{y + h - r:.3f} Q{x1:.3f} {y + h:.3f} {x1 - r:.3f} {y + h:.3f} '
                f'H{x0 + r:.3f} Q{x0:.3f} {y + h:.3f} {x0:.3f} {y + h - r:.3f} Z" fill="{SILK}"/>',
                (x0, y, x1, y + h), label or f"tab {s}"))
    text(xc, y + h / 2 + 0.02, s, h=th, fill=MASK, label=label or f"tab {s}")
    return x0, x1

def bracket(first, last, name=None, tab_at=None):
    """Pins first..last (0-based); view x: pin `first` is on the right. Tab kept inside the bracket."""
    half = lambda i: len(J7[i]) * CHAR_W * 0.85 / 2 + 0.3     # keep end ticks clear of wide codes
    xr = j7x[first] + max(0.92, half(first))
    xl = j7x[last] - max(0.92, half(last))
    poly(rounded([(xr, TICK_Y), (xr, BR_Y), (xl, BR_Y), (xl, TICK_Y)], 0.3), label=f"bracket {name or J7[first]}")
    if name:
        if tab_at is None:
            tab_at = (j7x[first] + j7x[last]) / 2
        w = len(name) * CHAR_W * 0.85 + 0.9
        tab_at = min(max(tab_at, xl + 0.3 + w / 2), xr - 0.3 - w / 2)
        hang_tab(tab_at, BR_Y, name)

bracket(0, 3, "EXP", (j7x[2] + j7x[3]) / 2)      # 3V3 + GP47/46/41; tab off-centre, clear of the J3 frame
bracket(4, 6, "PORT 2")
bracket(7, 9, "PORT 1")
bracket(10, 17, "TFT")

# J3 SWD / I2C: solid frame "A" round the connector, S-curve leader to a detail card with the white title
colA, colB = VX(11.70), VX(14.24)          # A: GND/SWCLK/SWDIO, B: 3V3/SDA/SCL (view: A right, B left)
FX0, FX1, FY0, FY1, FR = colB - 1.32, colA + 1.32, 3.9, 11.25, 0.6
poly(rrect_pts(FX0, FY0, FX1, FY1, FR), closed=True, label="J3 frame")

def badge(x, y, s, r=0.65, label="badge"):
    art.append((f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="{SILK}"/>', (x - r, y - r, x + r, y + r), label))
    text(x, y + 0.02, s, h=0.85, fill=MASK, label=label)


# detail card
TH = 1.0
CX0, CX1, CY0, CY1, CR, HEAD = 53.8, 66.8, 6.0, 13.0, 0.7, 1.35
poly(rrect_pts(CX0, CY0, CX1, CY1, CR), closed=True, label="J3 card")
art.append((f'<path d="M{CX0:.3f} {CY0 + HEAD:.3f} V{CY0 + CR:.3f} Q{CX0:.3f} {CY0:.3f} {CX0 + CR:.3f} {CY0:.3f} '
            f'H{CX1 - CR:.3f} Q{CX1:.3f} {CY0:.3f} {CX1:.3f} {CY0 + CR:.3f} V{CY0 + HEAD:.3f} Z" fill="{SILK}"/>',
            (CX0, CY0, CX1, CY0 + HEAD), "J3 card title"))
text((CX0 + CX1) / 2, CY0 + HEAD / 2 + 0.03, "SWD / I2C", h=0.9, fill=MASK, label="J3 card title")
mB, mA = 58.8, 60.8                          # mini columns: I2C (B) view-left, SWD (A) view-right
rows = [CY0 + HEAD + 1.2, CY0 + HEAD + 2.7, CY0 + HEAD + 4.2]
for i, y in enumerate(rows):
    if i == 0:
        poly([(mA - 0.45, y - 0.45), (mA + 0.45, y - 0.45), (mA + 0.45, y + 0.45), (mA - 0.45, y + 0.45)],
             closed=True, label="card pin1")
    else:
        poly(circle_pts(mA, y, 0.45), closed=True, label="card pin")
    poly(circle_pts(mB, y, 0.45), closed=True, label="card pin")
for y, a_, b_ in zip(rows, ["GND", "SWCLK", "SWDIO"], ["3V3", "SDA", "SCL"]):
    text(mA + 0.85, y, a_, h=TH, anchor="start")
    text(mB - 0.85, y, b_, h=TH, anchor="end")

# S-curve leader: frame left side -> card right side
def bez(p0, p1, p2, p3, n=24):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                  for a, b, c, d in zip(p0, p1, p2, p3)) for t in (k / n for k in range(n + 1))]
ys, ye = (FY0 + FY1) / 2, CY0 + HEAD + 2.7
xm, rr = (FX0 + CX1) / 2, 0.8                # orthogonal leader with rounded corners
poly([(FX0, ys)] + arc_pts(xm + rr, ys + rr, rr, 270, 180) + arc_pts(xm - rr, ye - rr, rr, 0, 90) + [(CX1, ye)],
     label="J3 leader")

# J9 (encoder, right edge in bottom view): codes left of the pins, vertical bracket, tab hanging left, text rotated
j9y = sorted(p_["y"] for p_ in pads if p_["ref"] == "J9")       # from the board
J9 = ["A", "B", "SW", "3V3", "GND"]
j9x = VX(1.60)
CODE_R = j9x - 0.85 - 0.25                       # right edge of the codes
for y, c in zip(j9y, J9):
    text(CODE_R, y, c, anchor="end")
BX = CODE_R - len("GND") * CHAR_W * 0.85 - 0.55  # bracket line x
yt, yb = j9y[0] - 0.75, j9y[-1] + 0.75
poly(rounded([(CODE_R, yt), (BX, yt), (BX, yb), (CODE_R, yb)], 0.3), label="J9 bracket")   # arms span the codes
name, th, h = "ENCODER", 0.85, 1.2
L = len(name) * CHAR_W * th + 0.9
yc, r = (yt + yb) / 2, 0.3
x0, x1 = BX - h, BX
art.append((f'<path d="M{x1:.3f} {yc - L / 2:.3f} V{yc + L / 2:.3f} H{x0 + r:.3f} Q{x0:.3f} {yc + L / 2:.3f} {x0:.3f} {yc + L / 2 - r:.3f} '
            f'V{yc - L / 2 + r:.3f} Q{x0:.3f} {yc - L / 2:.3f} {x0 + r:.3f} {yc - L / 2:.3f} Z" fill="{SILK}"/>',
            (x0, yc - L / 2, x1, yc + L / 2), "J9 tab"))
tx = (x0 + x1) / 2
art.append((f'<text x="{tx:.3f}" y="{yc + 0.36 * th:.3f}" font-size="{th * 1.36:.3f}" text-anchor="middle" font-family="{FONT}" '
            f'font-weight="600" font-stretch="condensed" fill="{MASK}" transform="rotate(-90 {tx:.3f} {yc:.3f})">{name}</text>',
            (x0, yc - L / 2, x1, yc + L / 2), "J9 tab"))

# J2 (switch matrix, bottom edge): group brackets above the pads, white tabs standing on them, no per-pin codes
j2x = [VX(1.60 + 2.54 * i) for i in range(33)]
J2_LINE, J2_TICK = 23.4, 23.75                   # square pad tops at 24.05
def bracket_up(first, last, name, min_e=0.6, tab_at=None, show_tab=True):
    """Pins first..last (0-based, pin 1 = index 0, on the view right). Tab stands on the line."""
    w = len(name) * CHAR_W * 0.85 + 0.9
    span = j2x[first] - j2x[last]
    e = max(min_e, (w + 0.6 - span) / 2)
    xr, xl = j2x[first] + e, j2x[last] - e
    if tab_at is not None:                      # off-centre tab: stretch the bracket to keep it inside
        xr, xl = max(xr, tab_at + w / 2 + 0.3), min(xl, tab_at - w / 2 - 0.3)
    poly(rounded([(xr, J2_TICK), (xr, J2_LINE), (xl, J2_LINE), (xl, J2_TICK)], 0.3), label=f"J2 bracket {name}")
    if not show_tab:
        return xl, xr
    xc, h, r = (tab_at if tab_at is not None else (xr + xl) / 2), 1.2, 0.3
    x0, x1, y = xc - w / 2, xc + w / 2, J2_LINE
    art.append((f'<path d="M{x0:.3f} {y:.3f} H{x1:.3f} V{y - h + r:.3f} Q{x1:.3f} {y - h:.3f} {x1 - r:.3f} {y - h:.3f} '
                f'H{x0 + r:.3f} Q{x0:.3f} {y - h:.3f} {x0:.3f} {y - h + r:.3f} Z" fill="{SILK}"/>',
                (x0, y - h, x1, y), f"J2 tab {name}"))
    text(xc, y - h / 2 + 0.02, name, h=0.85, fill=MASK, label=f"J2 tab {name}")
    return xl, xr

ends = [bracket_up(0, 1, "GND"),
        bracket_up(2, 9, "R0-7"), bracket_up(10, 11, "GND"),
        bracket_up(12, 27, "C0-15"), bracket_up(28, 29, "C16-17"), bracket_up(30, 32, "LED")]
for (l1, r1), (l2, r2) in zip(ends, ends[1:]):
    if l1 - r2 < 0.5:
        print(f"J2 brackets only {l1 - r2:.2f} mm apart near view x {l1:.1f}")

# ---------------------------------------------------------------- checks
def pad_box(p):
    if p["shape"] == "circle" or (p["shape"] == "oval" and abs(p["w"] - p["h"]) < 1e-6):
        return None
    w, h = p["w"], p["h"]
    if round(abs(p["ang"])) % 180 == 90:
        w, h = h, w
    return (p["x"] - w / 2, p["y"] - h / 2, p["x"] + w / 2, p["y"] + h / 2)

def box_dist(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)

def circ_dist(bx, cx, cy, r):
    dx = max(bx[0] - cx, 0, cx - bx[2])
    dy = max(bx[1] - cy, 0, cy - bx[3])
    return math.hypot(dx, dy) - r

def pad_dist_pt(px, py, p):
    pb = pad_box(p)
    if pb:
        return box_dist((px, py, px, py), pb)
    r = p["w"] / 2 if p["kind"] != "np_thru_hole" else p["drill"] / 2
    return math.hypot(px - p["x"], py - p["y"]) - r

def samples(pts, step=0.05):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        for k in range(n + 1):
            yield ax + (bx - ax) * k / n, ay + (by - ay) * k / n

problems, via_hits = {}, set()
for svg, bb, lab in art:
    if bb is None:
        continue
    for p in pads:
        pb = pad_box(p)
        r = max(p["w"], p["h"]) / 2 if p["kind"] != "np_thru_hole" else p["drill"] / 2
        d = box_dist(bb, pb) if pb else circ_dist(bb, p["x"], p["y"], r)
        if d < CLEAR:
            k = (lab, p["ref"], p["num"]); problems[k] = min(d, problems.get(k, 9))
    for vx, vy, vr in vias:
        if circ_dist(bb, vx, vy, vr) < 0:
            via_hits.add((lab, round(XM - vx, 2), vy))
for pts, sw, lab in strokes:
    for sx, sy in samples(pts):
        for p in pads:
            d = pad_dist_pt(sx, sy, p) - sw / 2
            if d < CLEAR:
                k = (lab, p["ref"], p["num"]); problems[k] = min(d, problems.get(k, 9))
        for vx, vy, vr in vias:
            if math.hypot(sx - vx, sy - vy) - vr - sw / 2 < 0:
                via_hits.add((lab, round(XM - vx, 2), vy))
problems = [f"{k[0]!r} {v:+.2f} mm from {k[1]} pad {k[2]}" for k, v in problems.items()]
via_hits = [f"{l!r} over via at ({x:.2f},{y:.2f})" for l, x, y in sorted(via_hits)]

# ---------------------------------------------------------------- render
x0, y0, x1, y1 = CROP
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" '
       f'width="{(x1 - x0) * 22:.0f}" height="{(y1 - y0) * 22:.0f}">',
       f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#e9e7e1"/>',
       f'<rect x="{-0.25}" y="0" width="85" height="26.5" fill="{MASK}"/>']
for e in edges:
    out.append('<polyline points="' + " ".join(f"{x:.3f},{y:.3f}" for x, y in e) + '" fill="none" stroke="#8a8a80" stroke-width="0.12"/>')
for vx, vy, vr in vias:
    out.append(f'<circle cx="{vx:.3f}" cy="{vy:.3f}" r="{vr:.3f}" fill="{VIA}"/>')
for p in pads:
    if p["kind"] == "np_thru_hole":
        out.append(f'<circle cx="{p["x"]:.3f}" cy="{p["y"]:.3f}" r="{p["drill"] / 2:.3f}" fill="{HOLE}"/>')
        continue
    if p["shape"] == "circle":
        out.append(f'<circle cx="{p["x"]:.3f}" cy="{p["y"]:.3f}" r="{p["w"] / 2:.3f}" fill="{CU}"/>')
    else:
        rr = min(p["w"], p["h"]) / 2 if p["shape"] == "oval" else (0.25 * min(p["w"], p["h"]) if p["shape"] == "roundrect" else 0)
        out.append(f'<rect x="{p["x"] - p["w"] / 2:.3f}" y="{p["y"] - p["h"] / 2:.3f}" width="{p["w"]:.3f}" height="{p["h"]:.3f}" '
                   f'rx="{rr:.3f}" fill="{CU}" transform="rotate({p["ang"]:.1f} {p["x"]:.3f} {p["y"]:.3f})"/>')
    if p["drill"]:
        out.append(f'<circle cx="{p["x"]:.3f}" cy="{p["y"]:.3f}" r="{p["drill"] / 2:.3f}" fill="{HOLE}"/>')
out += [a[0] for a in art]
out.append("</svg>")
open(OUT, "w", encoding="utf-8").write("\n".join(out))
print(f"{len(pads)} exposed pads, {len(vias)} vias, {len(art)} art items -> {OUT}")
print("CLEARANCE PROBLEMS:", len(problems))
for p in problems:
    print("  ", p)
print("over tented vias:", len(via_hits))
for v in via_hits:
    print("  ", v)
