"""Back-silkscreen art generator for the Leyden Jar V2 controller.

Usage:  python -E -P backsilk.py [board.kicad_pcb]
  (fontTools and shapely come from the user site-packages, so not -I)
Needs: fontTools, shapely; fonts in art/fonts (Barlow Condensed, SIL OFL 1.1, see fonts/OFL.txt).

Reads the board geometry (read-only) and builds the whole B.SilkS art as exact outlines:
text as Barlow glyph outlines (with GPOS kerning), strokes buffered to their width, white tabs with the text
knocked out. All art is defined in VIEW coordinates: millimetres as seen from the bottom of the board
(board x mirrored: vx = XM - x, vy = y), so text reads normally.

Outputs (next to this script):
  backsilk_preview.svg   bottom view: board, exposed copper, vias and the final silk outlines
  backsilk_board.svg     the silk in BOARD coordinates (mirrored), hole-free polygons, canvas origin at the
                         board origin: KiCad File > Import > Graphics onto B.SilkS at (0, 0), scale 1
                         (Konnect's import_svg_logo kept only one polygon over IPC on 2026-11-09)
  backsilk_board.json    the same polygons, to verify the import against the board file
Preview PNG (headless Edge):
  msedge --headless=new --disable-gpu --hide-scrollbars --window-size=1914,612 --screenshot=out.png file:///<abs path>/backsilk_preview.svg
"""
import json, math, os, re, sys

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon, box
from shapely.ops import split, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "Leyden_Jar.kicad_pcb")
CROP = (-1.0, -0.6, 86.0, 27.2)
XM = 84.5                                 # mirror axis: vx = XM - x
CLEAR = 0.15                              # silk to exposed copper (mm)
MIN_W = 0.15                              # narrowest silk line / knock-out gap reported as OK (mm)

MASK, SILK, CU, HOLE, VIA = "#1d3a2c", "#f2f2ee", "#c9cdd1", "#0b140f", "#2f5442"

def VX(x):
    return XM - x

# ---------------------------------------------------------------- fonts (glyph outlines, kerning)
class _FlatPen(BasePen):
    """Collects glyph contours as polylines (quadratic / cubic segments flattened)."""
    def __init__(self, gs, n=10):
        super().__init__(gs)
        self.rings, self.cur, self.n = [], [], n
    def _moveTo(self, p):
        self.cur = [p]
    def _lineTo(self, p):
        self.cur.append(p)
    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        self.cur += [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))
                     for t in (k / self.n for k in range(1, self.n + 1))]
    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        self.cur += [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
                           for a, b, c, d in zip(p0, p1, p2, p3)) for t in (k / self.n for k in range(1, self.n + 1))]
    def _closePath(self):
        if len(self.cur) > 2:
            self.rings.append(self.cur)
        self.cur = []
    _endPath = _closePath

class Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs, self.cmap = self.f.getGlyphSet(), self.f.getBestCmap()
        self.cap = self.f["OS/2"].sCapHeight
        self.hmtx = self.f["hmtx"]
        self.cache = {}
        self.subtables = []
        if "GPOS" in self.f:
            g = self.f["GPOS"].table
            idx = sorted({i for fr in g.FeatureList.FeatureRecord if fr.FeatureTag == "kern"
                          for i in fr.Feature.LookupListIndex})
            for i in idx:
                lk = g.LookupList.Lookup[i]
                for st in lk.SubTable:
                    if lk.LookupType == 9:
                        st = st.ExtSubTable
                    if getattr(st, "LookupType", 2) == 2 and st.Format in (1, 2):
                        self.subtables.append(st)

    def kern(self, a, b):
        for st in self.subtables:
            if a not in st.Coverage.glyphs:
                continue
            if st.Format == 1:
                ps = st.PairSet[st.Coverage.glyphs.index(a)]
                for r in ps.PairValueRecord:
                    if r.SecondGlyph == b:
                        return getattr(r.Value1, "XAdvance", 0) or 0
            else:
                c1 = st.ClassDef1.classDefs.get(a, 0)
                c2 = st.ClassDef2.classDefs.get(b, 0)
                v = st.Class1Record[c1].Class2Record[c2].Value1
                return getattr(v, "XAdvance", 0) or 0
        return 0

    def glyph(self, name):
        if name not in self.cache:
            pen = _FlatPen(self.gs)
            self.gs[name].draw(pen)
            g = Polygon()
            for r in pen.rings:                      # even-odd: counters cut out of their outer contour
                g = g.symmetric_difference(Polygon(r).buffer(0))
            self.cache[name] = g
        return self.cache[name]

    def layout(self, s):
        """[(glyph name, x)] and the total advance, in font units."""
        out, x, prev = [], 0, None
        for ch in s:
            g = self.cmap[ord(ch)]
            if prev:
                x += self.kern(prev, g)
            out.append((g, x))
            x += self.hmtx[g][0]
            prev = g
        return out, x

FONTS = {600: Font(os.path.join(HERE, "fonts", "BarlowCondensed-SemiBold.ttf")),
         700: Font(os.path.join(HERE, "fonts", "BarlowCondensed-Bold.ttf"))}

# Stroke widths (font units / cap height 700): SemiBold 100 horizontal, 116 vertical; Bold 121 / 141.
# JLCPCB wants >= 0.15 mm lines: white text below SMALL_BOLD uses Bold (0.173 x h, so h >= 0.9);
# knocked-out tab text stays SemiBold, which leaves wider silk counters inside the letters.
SMALL_BOLD = 1.07
CODE_H = 0.9         # pin codes
LETTER_GAP = 0.15    # minimum gap between neighbouring glyphs (mm): keeps letters apart, and keeps the silk
                     # between knocked-out letters printable; spacing is only added where a pair is closer

_runs = {}
def run(s, h=CODE_H, weight=600, knocked=False):
    """Glyph outlines of s in mm (origin at the left end of the baseline, y up) and the advance width."""
    key = (s, h, weight if knocked or h >= SMALL_BOLD else 700)
    if key not in _runs:
        f = FONTS[key[2]]
        k = h / f.cap
        glyphs, adv = f.layout(s)
        parts, shift, prev = [], 0.0, None
        for g, gx in glyphs:
            geom = affinity.affine_transform(f.glyph(g), [k, 0, 0, k, gx * k + shift, 0])
            if not geom.is_empty:
                if prev is not None:
                    d = prev.distance(geom)
                    if d < LETTER_GAP:
                        shift += LETTER_GAP - d
                        geom = affinity.translate(geom, LETTER_GAP - d)
                parts.append(geom)
                prev = geom
        _runs[key] = (unary_union(parts), adv * k + shift)
    return _runs[key]

def tw(s, h=CODE_H, weight=600, knocked=False):
    """Advance width of a string in mm, h = cap height."""
    return run(s, h, weight, knocked)[1]

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

# ---------------------------------------------------------------- art primitives (view coords, shapely geometry)
silk = []      # (geometry, label): white
knock = []     # (geometry, label): cut out of the white (text in tabs, '!' in triangles)

def text(x, y, s, h=CODE_H, anchor="middle", fill=SILK, weight=600, label=None):
    """(x, y) = anchor point on the cap-height centre line. Returns the advance width (mm)."""
    geom, w = run(s, h, weight, knocked=fill != SILK)
    x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
    geom = affinity.affine_transform(geom, [1, 0, 0, -1, x0, y + h / 2])
    (silk if fill == SILK else knock).append((geom, label or s))
    return w

TAB_T, TAB_H = 1.0, 1.4   # knocked-out tab text cap height and tab height (counters >= ~0.15 mm)

def rbox(x0, y0, x1, y1, r, corners="tl tr br bl", n=8):
    """Box with the listed corners rounded (view: t = small y)."""
    cs = corners.split()
    pts = []
    for c, (cx, cy), a0 in (("tl", (x0, y0), 180), ("tr", (x1, y0), 270), ("br", (x1, y1), 0), ("bl", (x0, y1), 90)):
        if c in cs and r > 0:
            ox = cx + (r if c[1] == "l" else -r)
            oy = cy + (r if c[0] == "t" else -r)
            pts += [(ox + r * math.cos(math.radians(a0 + 90 * i / n)), oy + r * math.sin(math.radians(a0 + 90 * i / n)))
                    for i in range(n + 1)]
        else:
            pts.append((cx, cy))
    return Polygon(pts)

def rect(x0, y0, x1, y1, r=0.0, label="rect"):
    silk.append((rbox(x0, y0, x1, y1, r), label))

def poly(pts, sw=0.15, closed=False, label="line"):
    line = LineString(list(pts) + ([pts[0]] if closed else []))
    silk.append((line.buffer(sw / 2, quad_segs=6), label))

def arc_pts(cx, cy, r, a0, a1, n=10):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]

def rrect_pts(x0, y0, x1, y1, r):
    return (arc_pts(x1 - r, y0 + r, r, -90, 0) + arc_pts(x1 - r, y1 - r, r, 0, 90) +
            arc_pts(x0 + r, y1 - r, r, 90, 180) + arc_pts(x0 + r, y0 + r, r, 180, 270))

def circle_pts(cx, cy, r):
    return arc_pts(cx, cy, r, 0, 360, 24)

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

def tab(xc, yc, s, h=TAB_H, th=TAB_T, padx=0.45, label=None):
    """Free-standing white tab, all corners rounded, text knocked out."""
    w = tw(s, th, knocked=True) + 2 * padx
    rect(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2, r=0.25, label=label or f"tab {s}")
    text(xc, yc, s, h=th, fill=MASK, label=label or f"tab {s}")

def hang_tab(xc, y, s, h=TAB_H, th=TAB_T, padx=0.45, r=0.3, label=None):
    """White tab hanging from a line at y: square top, rounded bottom corners."""
    w = tw(s, th, knocked=True) + 2 * padx
    x0, x1 = xc - w / 2, xc + w / 2
    silk.append((rbox(x0, y, x1, y + h, r, "bl br"), label or f"tab {s}"))
    text(xc, y + h / 2, s, h=th, fill=MASK, label=label or f"tab {s}")
    return x0, x1

# ---------------------------------------------------------------- the design
# J7: codes, a bracket per group, white tab hanging from the bracket
J7 = ["3V3", "47", "46", "41", "5V", "GND", "32", "5V", "GND", "45",
      "GND", "3V3", "SCK", "MOSI", "RST", "DC", "CS", "BLK"]
j7x = [VX(11.6 + 2.54 * i) for i in range(18)]
CODE_Y, BR_Y, TICK_Y = 2.87, 3.56, 2.55     # codes >= 0.15 mm from pads and bracket
for x, s in zip(j7x, J7):
    text(x, CODE_Y, s)

def bracket(first, last, name=None, tab_at=None):
    """Pins first..last (0-based); view x: pin `first` is on the right. Tab kept inside the bracket."""
    half = lambda i: tw(J7[i]) / 2 + 0.3                  # keep end ticks clear of wide codes
    xr = j7x[first] + max(0.92, half(first))
    xl = j7x[last] - max(0.92, half(last))
    poly(rounded([(xr, TICK_Y), (xr, BR_Y), (xl, BR_Y), (xl, TICK_Y)], 0.3), label=f"bracket {name or J7[first]}")
    if name:
        if tab_at is None:
            tab_at = (j7x[first] + j7x[last]) / 2
        w = tw(name, TAB_T, knocked=True) + 0.9
        tab_at = min(max(tab_at, xl + 0.3 + w / 2), xr - 0.3 - w / 2)
        hang_tab(tab_at, BR_Y, name)

bracket(0, 3, "EXP", (j7x[2] + j7x[3]) / 2)      # 3V3 + GP47/46/41; tab off-centre, clear of the J3 frame
bracket(4, 6, "PORT 2")
bracket(7, 9, "PORT 1")
bracket(10, 17, "TFT")

# J3 SWD / I2C: solid frame round the connector, orthogonal leader to a detail card with a white title band
colA, colB = VX(11.70), VX(14.24)          # A: GND/SWCLK/SWDIO, B: 3V3/SDA/SCL (view: A right, B left)
FX0, FX1, FY0, FY1, FR = colB - 1.32, colA + 1.32, 3.9, 11.25, 0.6
poly(rrect_pts(FX0, FY0, FX1, FY1, FR), closed=True, label="J3 frame")

TH = 1.0
CX0, CX1, CY0, CY1, CR, HEAD = 45.2, 58.2, 6.0, 13.0, 0.7, 1.5
poly(rrect_pts(CX0, CY0, CX1, CY1, CR), closed=True, label="J3 card")
silk.append((rbox(CX0, CY0, CX1, CY0 + HEAD, CR, "tl tr"), "J3 card title"))
text((CX0 + CX1) / 2, CY0 + HEAD / 2, "SWD / I2C", h=TAB_T, fill=MASK, label="J3 card title")
mB, mA = CX0 + 5.0, CX0 + 7.0                          # mini columns: I2C (B) view-left, SWD (A) view-right
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

ys, ye = (FY0 + FY1) / 2, CY0 + HEAD + 2.7
xm, rr = (FX0 + CX1) / 2, 0.8                # orthogonal leader with rounded corners: frame -> card
poly([(FX0, ys)] + arc_pts(xm + rr, ys + rr, rr, 270, 180) + arc_pts(xm - rr, ye - rr, rr, 0, 90) + [(CX1, ye)],
     label="J3 leader")

# J9 (encoder, right edge in bottom view): codes left of the pins, vertical bracket, horizontal tab on its left
j9y = sorted(p_["y"] for p_ in pads if p_["ref"] == "J9")       # from the board
J9 = ["A", "B", "SW", "3V3", "GND"]
j9x = VX(1.60)
CODE_R = j9x - 0.85 - 0.25                       # right edge of the codes
for y, c in zip(j9y, J9):
    text(CODE_R, y, c, anchor="end")
BX = CODE_R - max(tw(c) for c in J9) - 0.55      # bracket line x
yt, yb = j9y[0] - 0.75, j9y[-1] + 0.75
poly(rounded([(CODE_R, yt), (BX, yt), (BX, yb), (CODE_R, yb)], 0.3), label="J9 bracket")   # arms span the codes
name, th, h = "ENCODER", TAB_T, TAB_H              # horizontal tab flying left from the bracket line, mid-height
L = tw(name, th, knocked=True) + 0.9
yc = (yt + yb) / 2
silk.append((rbox(BX - L, yc - h / 2, BX, yc + h / 2, 0.3, "tl bl"), "J9 tab"))
text(BX - L / 2, yc, name, h=th, fill=MASK, label="J9 tab")
J9_TAB_X0 = BX - L

# J2 (switch matrix, bottom edge): group brackets above the pads, white tabs standing on them, no per-pin codes
j2x = [VX(1.60 + 2.54 * i) for i in range(33)]
J2_LINE, J2_TICK = 23.4, 23.75                   # square pad tops at 24.05
# Pin 1 is on the view right, so every group reads from its highest index (left) to index 0 (right): the index
# of each end pin stands on the bracket line right above that pin, the group name sits in a tab in the middle.
J2_IDX_Y = J2_LINE - 0.075 - 0.17 - CODE_H / 2   # index codes >= 0.15 mm above the bracket line (round digits overshoot)

def bracket_up(first, last, name=None, idx=None, min_e=0.6):
    """Pins first..last (0-based, pin 1 = index 0, on the view right). Tab stands on the line.
    idx = (label above pin `first`, label above pin `last`)."""
    w = tw(name, TAB_T, knocked=True) + 0.9 if name else 0.0
    span = j2x[first] - j2x[last]
    e = max(min_e, (w + 0.6 - span) / 2)
    xr, xl = j2x[first] + e, j2x[last] - e
    lab = name or "/".join(idx)
    poly(rounded([(xr, J2_TICK), (xr, J2_LINE), (xl, J2_LINE), (xl, J2_TICK)], 0.3), label=f"J2 bracket {lab}")
    if name:
        xc, h = (xr + xl) / 2, TAB_H
        silk.append((rbox(xc - w / 2, J2_LINE - h, xc + w / 2, J2_LINE, 0.3, "tl tr"), f"J2 tab {name}"))
        text(xc, J2_LINE - h / 2, name, h=TAB_T, fill=MASK, label=f"J2 tab {name}")
    if idx:
        text(j2x[first], J2_IDX_Y, idx[0], label=f"J2 idx {lab} {idx[0]}")
        text(j2x[last], J2_IDX_Y, idx[1], label=f"J2 idx {lab} {idx[1]}")
    return xl, xr

ends = [bracket_up(0, 1, "GND"),
        bracket_up(2, 9, "ROW", ("0", "7")), bracket_up(10, 11, "GND"),
        bracket_up(12, 27, "COL", ("0", "15")), bracket_up(28, 29, idx=("16", "17")),
        bracket_up(30, 32, "LED", ("0", "2"))]
for (l1, r1), (l2, r2) in zip(ends, ends[1:]):
    if l1 - r2 < 0.5:
        print(f"J2 brackets only {l1 - r2:.2f} mm apart near view x {l1:.1f}")

# J4 Ext port (2x4, left side in bottom view): card round the connector, white title band, codes on both sides.
# Odd pins (D-, 5V, PS2 EN, 3V3) on the view-right column, even pins on the view-left column.
j4 = {p_["num"]: (p_["x"], p_["y"]) for p_ in pads if p_["ref"] == "J4"}
j4L, j4R = j4["2"][0], j4["1"][0]
j4y = [j4[str(n)][1] for n in (1, 3, 5, 7)]
J4L = ["USB D+", "EN / CLK", "PULSE / DATA", "GND"]   # solenoid / PS/2 roles, order given by the card title
J4R = ["USB D-", "5V", "PS2 EN", "3V3"]
for y, l_, r_ in zip(j4y, J4L, J4R):
    text(j4L - 1.1, y, l_, anchor="end")
    text(j4R + 1.1, y, r_, anchor="start")
KX0 = j4L - 1.1 - max(tw(c) for c in J4L) - 0.6
KX1 = j4R + 1.1 + max(tw(c) for c in J4R) - 0.0 + 0.6
KH = 1.5
KY0, KY1 = j4y[0] - 0.85 - 0.2 - KH, j4y[-1] + 0.85 + 0.45
poly(rrect_pts(KX0, KY0, KX1, KY1, CR), closed=True, label="J4 card")
silk.append((rbox(KX0, KY0, KX1, KY0 + KH, CR, "tl tr"), "J4 card title"))
J4_TITLE = "EXT PORT · USB / SOL / PS2"
text((KX0 + KX1) / 2, KY0 + KH / 2, J4_TITLE, h=TAB_T, fill=MASK, label="J4 card title")
ydiv = (j4y[0] + j4y[1]) / 2                      # USB row (pins 1-2, key jumper) set apart
poly([(KX0 + 0.5, ydiv), (KX1 - 0.5, ydiv)], label="J4 USB divider")

# Solenoid cable warning: the solenoid board dies if its cable is plugged in reversed (red wire must go on the
# square 5V pin, J4 pin 3). Warning triangle next to the pin, repeated with a short note in the top-left corner.
def warn(cx, cy, side, label="warning"):
    """Upright filled warning triangle (rounded corners), '!' knocked out. (cx, cy) = centre of its box."""
    sw = 0.2                                     # rounding radius sw / 2
    s = side - sw * 1.73                         # keep the outer size equal to `side`
    hgt = s * 0.866
    top, bot = cy - hgt / 2, cy + hgt / 2
    tri = Polygon([(cx, top), (cx + s / 2, bot), (cx - s / 2, bot)])
    silk.append((tri.buffer(sw / 2, quad_segs=6), label))
    bw = max(0.18, s * 0.13)                     # '!' bar and dot
    y0, y1, yd = top + hgt * 0.30, top + hgt * 0.66, top + hgt * 0.82
    knock.append((LineString([(cx, y0 + bw / 2), (cx, y1 - bw / 2)]).buffer(bw / 2, quad_segs=6), label))
    knock.append((Point(cx, yd).buffer(bw * 0.6, quad_segs=6), label))

warn(j4R + 1.1 + tw("5V") + 0.25 + 0.9, j4y[1], 1.8, label="J4 5V warning")      # right of the "5V" code
# note: top-left corner (view), between the board edge and H2's square pad, centred on H2 vertically
NOTE = ["SOLENOID", "CABLE", "RED WIRE", "ON 5V"]
NH, NP, TRI, GAP_T = 1.0, 1.3, 2.1, 0.6
h2 = [p_ for p_ in pads if p_["ref"] == "H2"][0]
NX = (-0.25 + 0.45 + h2["x"] - h2["w"] / 2 - 0.45) / 2                # board edge .. H2 pad left edge
grp = TRI * 0.866 + GAP_T + (len(NOTE) - 1) * NP + NH
ny = h2["y"] - grp / 2
warn(NX, ny + TRI * 0.866 / 2, TRI, label="solenoid note warning")
for i, line in enumerate(NOTE):
    text(NX, ny + TRI * 0.866 + GAP_T + NH / 2 + i * NP, line, h=NH, label="solenoid note")

# RUN / BOOT (bottom-side B3U buttons SW1 = RUN, SW2 = BOOT): white tab under each pad pair
for ref, s_ in (("SW1", "RUN"), ("SW2", "BOOT")):
    bx_ = [p_ for p_ in pads if p_["ref"] == ref]
    tab(bx_[0]["x"], max(p_["y"] for p_ in bx_) + 0.95 + 0.85, s_, padx=0.28, label=f"tab {s_}")

# Board identity: Rico logo, name, description, version
LOGO_SRC = json.load(open(os.path.join(HERE, "rico_logo_view.json"), encoding="utf-8"))["polygons"]
def logo(cx, cy, size):
    g = unary_union([Polygon(q).buffer(0) for q in LOGO_SRC])
    x0, y0, x1, y1 = g.bounds
    k = size / max(x1 - x0, y1 - y0)
    g = affinity.affine_transform(g, [k, 0, 0, k, cx - (x0 + x1) / 2 * k, cy - (y0 + y1) / 2 * k])
    silk.append((g, "logo"))

# Two blocks on one band between the J4 card and the J9 tab, sharing one vertical centre and spaced with
# equal gaps (left margin = middle gap = right margin).
TITLE, SUB, VER = "The Leyden Jar", "Beam Spring and Model F controller", "V2 · REV 1 · 2026"
CREDIT, LOGO = ["Designed with love", "by"], 8.0
TITLE_W = max(tw(TITLE, 2.3, 700), tw(SUB, 0.95))
CREDIT_W = max(tw(c, 1.0) for c in CREDIT)
BAND_L, BAND_R = KX1, J9_TAB_X0                 # J4 card right edge, J9 tab left edge
GAP = (BAND_R - BAND_L - TITLE_W - (CREDIT_W + 0.8 + LOGO)) / 3
MID = 17.0                                      # common vertical centre
TX = BAND_L + GAP
VOFF = 4.41                                     # subtitle descenders >= 0.15 mm above the version tab
ROW = MID - (1.15 + VOFF + TAB_H / 2) / 2 + 1.15     # title cap top .. version tab bottom centred on MID
text(TX, ROW, TITLE, h=2.3, anchor="start", weight=700, label="title")
text(TX, ROW + 2.75, SUB, h=0.95, anchor="start", label="subtitle")
VY = ROW + VOFF                                 # version tab on the line below the subtitle
VW = tw(VER, TAB_T, knocked=True) + 2.4
rect(TX, VY - TAB_H / 2, TX + VW, VY + TAB_H / 2, r=0.25, label="version tab")
text(TX + VW / 2, VY, VER, h=TAB_T, fill=MASK, label="version tab")
LX = BAND_R - GAP - LOGO / 2
logo(LX, MID, LOGO)
text(LX - LOGO / 2 - 0.8, MID - 0.75, CREDIT[0], h=1.0, anchor="end", label="credit")
text(LX - LOGO / 2 - 0.8, MID + 0.75, CREDIT[1], h=1.0, anchor="end", label="credit")
print(f"identity: gap {GAP:.2f} mm, title x {TX:.2f}, logo centre x {LX:.2f}")
print(f"J4 title band: {tw(J4_TITLE, TAB_T, knocked=True):.2f} mm of text in {KX1 - KX0:.2f} mm")

# ---------------------------------------------------------------- final geometry
ART = unary_union([g for g, _ in silk]).difference(unary_union([g for g, _ in knock]))
ART = ART.simplify(0.002)

# ---------------------------------------------------------------- checks
def pad_geom(p):
    if p["kind"] == "np_thru_hole":
        return Point(p["x"], p["y"]).buffer(max(p["drill"], p["w"]) / 2, quad_segs=16)
    if p["shape"] == "circle":
        return Point(p["x"], p["y"]).buffer(p["w"] / 2, quad_segs=16)
    w, h = p["w"], p["h"]
    if p["shape"] == "oval":
        a = (w - h) / 2 if w > h else 0
        b = (h - w) / 2 if h > w else 0
        g = LineString([(p["x"] - a, p["y"] - b), (p["x"] + a, p["y"] + b)]).buffer(min(w, h) / 2, quad_segs=16)
    else:
        g = box(p["x"] - w / 2, p["y"] - h / 2, p["x"] + w / 2, p["y"] + h / 2)
    return affinity.rotate(g, p["ang"], origin=(p["x"], p["y"]))

copper = [(pad_geom(p), p) for p in pads]
problems = {}
for g, lab in silk:
    for pg, p in copper:
        d = g.distance(pg)
        if d < CLEAR:
            k = (lab, p["ref"], p["num"])
            problems[k] = min(d, problems.get(k, 9))
via_hits = sum(1 for vx, vy, vr in vias if ART.intersects(Point(vx, vy).buffer(vr)))
thin = ART.difference(ART.buffer(-MIN_W / 2 + 0.005).buffer(MIN_W / 2 - 0.005 + 1e-4))   # 0.15 lines pass
gaps = ART.buffer(MIN_W / 2 - 0.005).buffer(-MIN_W / 2 + 0.005 - 1e-4).difference(ART)
def spots(g, label):
    gs = [p for p in getattr(g, "geoms", [g]) if not p.is_empty and p.area > 2e-4]
    print(f"{label}: {len(gs)}")
    for p in sorted(gs, key=lambda q: -q.area)[:12]:
        c = p.centroid
        print(f"   area {p.area * 1e3:6.2f} um^2*1e3 at view ({c.x:.2f}, {c.y:.2f})")

# ---------------------------------------------------------------- outputs
def svg_path(g, fmt="{:.4f}"):
    out = []
    for p in getattr(g, "geoms", [g]):
        for ring in [p.exterior] + list(p.interiors):
            out.append("M" + " L".join(f"{fmt.format(x)} {fmt.format(y)}" for x, y in ring.coords[:-1]) + "Z")
    return "".join(out)

x0, y0, x1, y1 = CROP
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" '
       f'width="{(x1 - x0) * 22:.0f}" height="{(y1 - y0) * 22:.0f}">',
       f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#e9e7e1"/>',
       f'<rect x="{-0.25}" y="0" width="85" height="26.5" fill="{MASK}"/>']
for e in edges:
    out.append('<polyline points="' + " ".join(f"{x:.3f},{y:.3f}" for x, y in e) + '" fill="none" stroke="#8a8a80" stroke-width="0.12"/>')
for vx, vy, vr in vias:
    out.append(f'<circle cx="{vx:.3f}" cy="{vy:.3f}" r="{vr:.3f}" fill="{VIA}"/>')
for pg, p in copper:
    out.append(f'<path d="{svg_path(pg, "{:.3f}")}" fill="{HOLE if p["kind"] == "np_thru_hole" else CU}"/>')
    if p["drill"] and p["kind"] != "np_thru_hole":
        out.append(f'<circle cx="{p["x"]:.3f}" cy="{p["y"]:.3f}" r="{p["drill"] / 2:.3f}" fill="{HOLE}"/>')
out.append(f'<path d="{svg_path(ART)}" fill="{SILK}" fill-rule="evenodd"/>')
out.append("</svg>")
open(os.path.join(HERE, "backsilk_preview.svg"), "w", encoding="utf-8").write("\n".join(out))

# board coordinates (x mirrored back), split into hole-free polygons for the import
def fracture(p):
    if not p.interiors:
        return [p]
    xs = sorted({round(Polygon(h).representative_point().x, 4) for h in p.interiors})
    _, ymin, _, ymax = p.bounds
    pieces = split(p, MultiLineString([[(x, ymin - 1), (x, ymax + 1)] for x in xs])).geoms
    return [q for piece in pieces for q in fracture(piece)]

board_art = affinity.affine_transform(ART, [-1, 0, 0, 1, XM, 0])
polys = [q for p in getattr(board_art, "geoms", [board_art]) for q in fracture(p)]
bx0, by0, bx1, by1 = board_art.bounds
with open(os.path.join(HERE, "backsilk_board.svg"), "w", encoding="utf-8") as f:
    # canvas origin = board origin, so an import at (0, 0) and scale 1 puts the art in place
    W, H = math.ceil(bx1) + 1, math.ceil(by1) + 1
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n')
    for q in polys:
        f.write(f'<path d="{svg_path(q)}" fill="#000000"/>\n')
    f.write("</svg>\n")
json.dump({"bounds": [bx0, by0, bx1, by1],
           "polygons": [[[round(x, 4), round(y, 4)] for x, y in q.exterior.coords[:-1]] for q in polys]},
          open(os.path.join(HERE, "backsilk_board.json"), "w"), separators=(",", ":"))

print(f"{len(pads)} exposed pads, {len(vias)} vias, {len(silk)} silk items, {len(knock)} knock-outs")
print(f"board art: {len(polys)} polygons, {sum(len(q.exterior.coords) for q in polys)} points, "
      f"art bounds x {bx0:.4f}..{bx1:.4f} y {by0:.4f}..{by1:.4f}; SVG canvas origin = board origin")
print("CLEARANCE PROBLEMS:", len(problems))
for (lab, ref, num), v in problems.items():
    print(f"   {lab!r} {v:+.3f} mm from {ref} pad {num}")
print("tented vias under silk:", via_hits)
spots(thin, f"silk features narrower than {MIN_W} mm")
spots(gaps, f"knock-out gaps narrower than {MIN_W} mm")
