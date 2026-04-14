import re
import io
from PIL import Image, ImageDraw, ImageFont


# ─────────────────────────────────────────────────────────────────
#  PARSING
# ─────────────────────────────────────────────────────────────────


def parse_intervals(free_str: str, utc_offset: float = 0) -> list[tuple[float, float]]:
    tokens = re.findall(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", free_str)
    if not tokens:
        raise ValueError(f"No valid intervals found in: {free_str!r}")

    result = []
    for s_str, e_str in tokens:
        s_local = float(s_str)
        e_local = float(e_str)

        if s_local < 0 or s_local > 48 or e_local < 0 or e_local > 48:
            raise ValueError(f"Hours must be 0-48, got {s_local}-{e_local}")

        if e_local <= s_local:
            e_local += 24

        s_utc = s_local - utc_offset
        e_utc = e_local - utc_offset

        while s_utc < 0:
            s_utc += 24
            e_utc += 24
        while s_utc >= 24:
            s_utc -= 24
            e_utc -= 24

        result.append((s_utc, e_utc))

    return result


# ─────────────────────────────────────────────────────────────────
#  CANVAS
# ─────────────────────────────────────────────────────────────────


class _Canvas:
    def __init__(self, w, h, bg):
        self.img = Image.new("RGBA", (w, h), _hex(bg))
        self.draw = ImageDraw.Draw(self.img, "RGBA")
        self.w, self.h = w, h

    def rect(self, x, y, w, h, color, radius=0, alpha=255):
        if w <= 0 or h <= 0:
            return
        args = [x, y, x + w, y + h]
        c = _hex(color, alpha)
        if radius:
            self.draw.rounded_rectangle(args, radius=radius, fill=c)
        else:
            self.draw.rectangle(args, fill=c)

    def line(self, x1, y1, x2, y2, color, width=1, alpha=255):
        self.draw.line([x1, y1, x2, y2], fill=_hex(color, alpha), width=width)

    def text(self, x, y, s, font, color, anchor="la", alpha=255):
        self.draw.text(
            (x, y), str(s), font=font, fill=_hex(color, alpha), anchor=anchor
        )

    def text_w(self, s, font):
        bb = font.getbbox(str(s))
        return bb[2] - bb[0]

    def save_png(self, path):
        self.img.convert("RGB").save(path)

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.img.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()


def _hex(c, alpha=255):
    if isinstance(c, tuple):
        return (*c[:3], alpha)
    h = c.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, alpha)


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf".format(
            "-Bold" if bold else ""
        ),
        "/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf".format(
            "Bold" if bold else "Regular"
        ),
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _fmt_offset(offset: float) -> str:
    sign = "+" if offset >= 0 else "-"
    abs_off = abs(offset)
    h = int(abs_off)
    m = int(round((abs_off - h) * 60))
    if m:
        return f"UTC{sign}{h}:{m:02d}"
    return f"UTC{sign}{h}"


# ─────────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────────

_BG = "#2B2D31"  # Discord dark mode background
_HDR = "#232428"  # header background
_TRACK = "#1E1F22"  # empty hour block
_SEP = "#3A3C41"  # separator lines
_TEXT = "#DCDDDE"  # primary text
_MUTED = "#72767D"  # secondary text (UTC badge, ruler)
_ACCENT = "#E87D00"  # orange - used for ALL availability blocks


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────


def _available_hours(intervals: list[tuple[float, float]]) -> set[int]:
    """Return the set of hours (0-23) covered by any interval."""
    flat = []
    for s, e in intervals:
        if e <= 24:
            flat.append((s, e))
        else:
            flat.append((s, 24.0))
            flat.append((0.0, e - 24.0))

    hours = set()
    for h in range(24):
        for s, e in flat:
            if s < h + 1 and e > h:
                hours.add(h)
                break
    return hours


# ─────────────────────────────────────────────────────────────────
#  RENDERER
# ─────────────────────────────────────────────────────────────────


def _render(users_parsed: list[dict], output_path: str | None, display_offset: float = 0) -> bytes | str:
    N = len(users_parsed)

    # ── Dimensions ────────────────────────────────────────────────
    # 24 equal-width blocks across the chart area.
    # Canvas sized for Discord embed (~460-520px display).
    NAME_W = 110  # right edge of name column
    CHART_X = NAME_W + 14  # = 124
    PAD_R = 14
    BLOCK_W = 14  # per-hour block pitch (including 2px gap)
    BLOCK_VIS = 12  # visible block width
    BLOCK_H = 22  # block height
    BLOCK_R = 4  # corner radius
    PAD_T = 46  # header (title + ruler)
    PAD_B = 14
    ROW_H = 46  # per-user row height
    W = CHART_X + 24 * BLOCK_W + PAD_R  # = 124 + 336 + 14 = 474
    CHART_H = N * ROW_H
    H = PAD_T + CHART_H + PAD_B

    F_TITLE = _font(17, bold=True)
    F_LABEL = _font(16, bold=True)
    F_RULER = _font(13)

    cv = _Canvas(W, H, _BG)

    def bx(h):
        """Left x of hour block h."""
        return CHART_X + h * BLOCK_W

    def ry(i):
        return PAD_T + i * ROW_H

    # ── Header ────────────────────────────────────────────────────
    cv.rect(0, 0, W, PAD_T, _HDR)

    tz_label = _fmt_offset(display_offset)
    cv.text(14, 16, "Availability", F_TITLE, _TEXT, anchor="lm")
    cv.text(W - PAD_R, 16, tz_label, F_TITLE, _ACCENT, anchor="rm")

    # Ruler labels at 00, 06, 12, 18 - centered above their block
    for h in (0, 6, 12, 18):
        cx = bx(h) + BLOCK_VIS // 2
        cv.text(cx, PAD_T - 6, f"{h:02d}", F_RULER, _MUTED, anchor="mb")

    # Header bottom border
    cv.line(0, PAD_T, W, PAD_T, _SEP, width=1)

    # ── Rows ──────────────────────────────────────────────────────
    for i, p in enumerate(users_parsed):
        y = ry(i)
        yc = y + ROW_H // 2
        block_y = yc - BLOCK_H // 2
        avail = _available_hours(p["intervals"])

        cv.text(NAME_W, yc, p["id"], F_LABEL, _TEXT, anchor="rm")

        # 24 hour blocks
        for h in range(24):
            color = _ACCENT if h in avail else _TRACK
            cv.rect(bx(h), block_y, BLOCK_VIS, BLOCK_H, color, radius=BLOCK_R)

        # Row separator (skip after last row)
        if i < N - 1:
            cv.line(0, y + ROW_H, W, y + ROW_H, _SEP, width=1)

    # ── Output ────────────────────────────────────────────────────
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
    display_offset: float = 0,
) -> str | bytes:
    """
    Generate an availability chart PNG.

    Parameters
    ----------
    users : list of dicts
        "id"         : str
        "free"       : str   e.g. "9-17" or "1-3,5-6"
        "utc_offset" : int | float  (optional, default 0)

    output_path : str | None
        File path to save, or None to return raw PNG bytes.
    """
    if not users:
        raise ValueError("users list is empty")

    parsed = []
    for idx, u in enumerate(users):
        uid = str(u["id"])
        free = str(u["free"])
        offset = float(u.get("utc_offset", 0))
        parsed.append(
            {
                "id": uid,
                "intervals": parse_intervals(free, offset),
                "utc_offset": offset,
            }
        )

    return _render(parsed, output_path, display_offset)


# ─────────────────────────────────────────────────────────────────
#  QUICK TEST
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    users = [
        {"id": "alice", "free": "9-17", "utc_offset": 0},
        {"id": "bob", "free": "22-26", "utc_offset": 0},
        {"id": "carlos", "free": "23-3", "utc_offset": 0},
        {"id": "priya", "free": "20-28", "utc_offset": 0},
        {"id": "james", "free": "8-12,22-26", "utc_offset": +2},
    ]
    out = generate_chart(users, "availability.png")
    print(f"Saved -> {out}")
