"""
availability.py  —  Discord Availability Chart Generator
=========================================================

PUBLIC API
----------
    generate_chart(users, output_path="availability.png") -> str

    users: list of dicts with:
        - "id":        str   — Discord user ID or display name
        - "free":      str   — free intervals, e.g. "9-17", "1-3,5-6", "9-12 14-18"
        - "utc_offset": int | float  (optional, default 0)  e.g. +2, -5, 5.5

    Returns the output path on success.

INTERVAL FORMAT (flexible)
--------------------------
    Separators between intervals: comma or space  →  "9-17"  "1-3,5-6"  "1-3 5-6"
    Range separator: dash                          →  "9-17"
    Hours: integers 0–24                           →  "0-8,22-24"

EXAMPLE
-------
    from availability import generate_chart

    users = [
        {"id": "alice",   "free": "9-17",          "utc_offset":  0},
        {"id": "bob",     "free": "1-3,5-6",        "utc_offset": +2},
        {"id": "carlos",  "free": "10-13 15-20",    "utc_offset": -5},
        {"id": "priya",   "free": "9-17",            "utc_offset":  5.5},
    ]
    generate_chart(users, "availability.png")
"""

import re
import io
from PIL import Image, ImageDraw, ImageFont


# ─────────────────────────────────────────────────────────────────
#  PARSING
# ─────────────────────────────────────────────────────────────────

def parse_intervals(free_str: str, utc_offset: float = 0) -> list[tuple[float, float]]:
    """
    Parse a free-time string into a list of (start_utc, end_utc) tuples.
    Handles wrap-around (e.g. offset shifts past midnight).

    Examples:
        "9-17"           → [(9, 17)]
        "1-3,5-6"        → [(1, 3), (5, 6)]
        "1-3 5-6"        → [(1, 3), (5, 6)]
        "22-2"           → [(22, 24), (0, 2)]   (overnight)
    """
    tokens = re.findall(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', free_str)
    if not tokens:
        raise ValueError(f"No valid intervals found in: {free_str!r}")

    result = []
    for s_str, e_str in tokens:
        s_local = float(s_str)
        e_local = float(e_str)

        if s_local < 0 or s_local > 48 or e_local < 0 or e_local > 48:
            raise ValueError(f"Hours must be 0\u201348, got {s_local}-{e_local}")

        # if end <= start, treat as overnight wrap (e.g. "22-2" means 22:00 to 02:00 next day)
        if e_local <= s_local:
            e_local += 24

        # shift to UTC — keep as linear range, e may exceed 24 for overnight spans
        s_utc = s_local - utc_offset
        e_utc = e_local - utc_offset

        # normalise so s_utc lands in [0, 24)
        while s_utc < 0:
            s_utc += 24
            e_utc += 24
        while s_utc >= 24:
            s_utc -= 24
            e_utc -= 24

        result.append((s_utc, e_utc))   # s in [0,24); e may exceed 24 for overnight bars

    return result


# ─────────────────────────────────────────────────────────────────
#  CANVAS
# ─────────────────────────────────────────────────────────────────

class _Canvas:
    def __init__(self, w, h, bg):
        self.img  = Image.new("RGBA", (w, h), _hex(bg))
        self.draw = ImageDraw.Draw(self.img, "RGBA")
        self.w, self.h = w, h

    def rect(self, x, y, w, h, color, radius=0, alpha=255):
        if w <= 0 or h <= 0:
            return
        c = _hex(color, alpha)
        args = [x, y, x + w, y + h]
        if radius:
            self.draw.rounded_rectangle(args, radius=radius, fill=c)
        else:
            self.draw.rectangle(args, fill=c)

    def line(self, x1, y1, x2, y2, color, width=1, alpha=255):
        self.draw.line([x1, y1, x2, y2], fill=_hex(color, alpha), width=width)

    def text(self, x, y, s, font, color, anchor="la", alpha=255):
        self.draw.text((x, y), str(s), font=font, fill=_hex(color, alpha), anchor=anchor)

    def text_w(self, s, font):
        bb = font.getbbox(str(s))
        return bb[2] - bb[0]

    def save_png(self, path):
        self.img.convert("RGB").save(path, dpi=(120, 120))

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.img.convert("RGB").save(buf, format="PNG", dpi=(120, 120))
        return buf.getvalue()


def _hex(c, alpha=255):
    if isinstance(c, tuple):
        return (*c[:3], alpha)
    h = c.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, alpha)


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf".format("-Bold" if bold else ""),
        "/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf".format(
            "Bold" if bold else "Regular"),
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────
#  CHART RENDERER
# ─────────────────────────────────────────────────────────────────

# Palette — Discord embed background + orange scheme
_BG       = "#2B2D31"   # Discord embed background (dark mode)
_BG2      = "#232428"   # slightly darker panel
_ROW_ALT  = "#26282C"   # subtle alt row
_BORDER   = "#3A3C41"   # grid lines
_TEXT     = "#F2F3F5"   # primary text
_DIM      = "#C8873A"   # orange-tinted dim text
_DIMMER   = "#6B4E2A"   # muted orange

_ACCENT   = "#FF8C00"   # main orange
_OVERLAP  = "#FF6A00"   # overlap strip color

_COLORS   = ["#FF8C00","#FFA63D","#E86400","#FFB347",
             "#CC6600","#FFCF87","#FF7300","#F09000"]


def _render(users_parsed: list[dict], output_path: str | None) -> bytes | str:
    """
    users_parsed: list of {"id", "intervals": [(s,e),...], "color"}
    """
    N = len(users_parsed)

    # ── layout ──────────────────────────────────────────────────
    LABEL_W  = 220          # name column
    PAD_L    = LABEL_W + 20
    PAD_R    = 36
    PAD_T    = 100          # title + hour ruler
    PAD_B    = 36           # bottom margin
    ROW_H    = 100          # tall rows — easy to see at Discord size
    BAR_H    = 46           # thick bars
    BAR_R    = 8
    W        = 1000
    CHART_W  = W - PAD_L - PAD_R
    CHART_H  = N * ROW_H
    H        = PAD_T + CHART_H + PAD_B

    F_TITLE  = _font(26, bold=True)
    F_LABEL  = _font(24, bold=True)
    F_RULER  = _font(26)
    F_BAR    = _font(18, bold=True)

    cv = _Canvas(W, H, _BG)

    def hx(utc_h):
        return PAD_L + int((utc_h % 24) / 24 * CHART_W)

    def ry(i):
        return PAD_T + i * ROW_H

    # ── header + footer panels ───────────────────────────────────
    cv.rect(0, 0,         W, PAD_T,        "#222428")
    cv.rect(0, H - PAD_B, W, PAD_B,        "#222428")
    cv.rect(0, PAD_T - 4, W, 4,            _ACCENT)
    cv.rect(PAD_L, PAD_T, CHART_W, CHART_H, _BG2)

    # ── alternating rows ────────────────────────────────────────
    for i in range(N):
        if i % 2 == 0:
            cv.rect(PAD_L, ry(i), CHART_W, ROW_H, _ROW_ALT)

    # ── hour ruler — only mark 0, 6, 12, 18 ─────────────────────
    for h in range(0, 25):
        x     = hx(h)
        major = (h % 6 == 0)
        cv.line(x, PAD_T - 28, x, PAD_T + CHART_H,
                _ACCENT if major else _BORDER,
                width=3 if major else 1,
                alpha=200 if major else 60)
        if major and h < 24:
            cv.text(x + 5, PAD_T - 16, f"{h:02d}", F_RULER, _DIM, anchor="lm")

    # ── title ────────────────────────────────────────────────────
    cv.text(20, PAD_T // 2, "Availability", F_TITLE, _TEXT, anchor="lm")
    cv.text(W - PAD_R, PAD_T // 2, "UTC", F_TITLE, _ACCENT, anchor="rm")

    # ── rows ─────────────────────────────────────────────────────
    for i, p in enumerate(users_parsed):
        y   = ry(i)
        yc  = y + ROW_H // 2
        col = p["color"]

        # name
        cv.text(LABEL_W, yc, p["id"], F_LABEL, _TEXT, anchor="rm")

        # left color accent stripe
        cv.rect(LABEL_W + 4, y + 14, 5, ROW_H - 28, col, radius=2)

        # row divider
        cv.line(0, y + ROW_H, W, y + ROW_H, _BORDER, alpha=60)

        # bars — e_utc may exceed 24 for overnight spans; draw as two segments
        bar_y = yc - BAR_H // 2
        for s_utc, e_utc in p["intervals"]:
            # split into segments that fit within [0, 24]
            segments = []
            if e_utc <= 24:
                segments.append((s_utc, e_utc))
            else:
                segments.append((s_utc, 24.0))   # segment up to midnight
                segments.append((0.0, e_utc - 24.0))  # segment from midnight

            # build a readable label from the original span
            lbl = f"{int(s_utc):02d}-{int(e_utc % 24):02d}"

            for seg_s, seg_e in segments:
                x1 = hx(seg_s)
                x2 = hx(seg_e)
                bw = x2 - x1
                if bw <= 0:
                    continue
                cv.rect(x1, bar_y, bw, BAR_H, col, radius=BAR_R)
                lw = cv.text_w(lbl, F_BAR)
                if bw > lw + 16:
                    cv.text(x1 + bw // 2, yc, lbl, F_BAR, "#FFFFFF", anchor="mm")

    # ── output ──────────────────────────────────────────────────
    if output_path:
        cv.save_png(output_path)
        return output_path
    return cv.to_bytes()



# ─────────────────────────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────────────────────────

def generate_chart(
        users: list[dict],
        output_path: str | None = "availability.png",
) -> str | bytes:
    """
    Generate an availability chart PNG.

    Parameters
    ----------
    users : list of dicts
        Each dict must have:
            "id"         : str            — display name / Discord user ID
            "free"       : str            — interval string, e.g. "9-17" or "1-3,5-6"
        Optional:
            "utc_offset" : int | float    — UTC offset, e.g. 2 for UTC+2 (default 0)

    output_path : str | None
        File path to save the PNG.
        Pass None to return raw bytes instead (useful for discord.py File objects).

    Returns
    -------
    str   — output_path if output_path was given
    bytes — PNG bytes if output_path=None
    """
    if not users:
        raise ValueError("users list is empty")

    parsed = []
    for idx, u in enumerate(users):
        uid    = str(u["id"])
        free   = str(u["free"])
        offset = float(u.get("utc_offset", 0))
        color  = _COLORS[idx % len(_COLORS)]

        intervals = parse_intervals(free, offset)
        parsed.append({"id": uid, "intervals": intervals, "color": color})

    return _render(parsed, output_path)


# ─────────────────────────────────────────────────────────────────
#  QUICK TEST  (python availability.py)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    users = [
        {"id": "alice",  "free": "9-17",   "utc_offset":  0},   # normal
        {"id": "bob",    "free": "22-26",  "utc_offset":  0},   # explicit next-day hours
        {"id": "carlos", "free": "23-3",   "utc_offset":  0},   # shorthand overnight
        {"id": "priya",  "free": "20-28",  "utc_offset":  0},   # long overnight span
        {"id": "james",  "free": "8-12,22-26", "utc_offset": +2}, # mixed with offset
    ]
    out = generate_chart(users, "availability.png")
    print(f"Saved → {out}")