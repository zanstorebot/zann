import asyncio
import math
import os
from datetime import datetime

import aiofiles
import aiohttp
import numpy as np
import pytz
from PIL import (Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter,
                 ImageFont, ImageOps)

from database import state
from logs import logger

from .buttons import ButtonUtils
from .tools import Tools

# ===========================================================================
#  PENGATURAN  -  edit angka di bagian ini saja, lalu restart bot
#  (transparansi memakai skala 0-255: 0 = hilang/bening, 255 = pekat)
# ===========================================================================

# --- File & font -----------------------------------------------------------
FONT_BOLD = "storage/cache/SFUIDisplay-Bold.ttf"        # judul lagu
FONT_REGULAR = "storage/cache/SFUIDisplay-Regular.ttf"  # teks lainnya
BG_PATH = "storage/cache/lock_bg.jpg"   # foto latar (pemandangan)
BG_DIM = 0.80                           # kecerahan latar: 1.0 asli, makin kecil makin gelap

# --- Teks pojok kiri atas (alicemusic) -------------------------------------
BRAND = "Alice Music"
BRAND_SIZE = 40         # ukuran teks
BRAND_X = 60            # posisi kiri
BRAND_Y = 56            # posisi atas (titik tengah teks)

# --- Tanggal tengah atas & jam ----------------------------------------------
TZ = pytz.timezone("Asia/Jakarta")
CLOCK_24H = False       # False = 9:05, True = 09:05
DATE_SIZE = 44          # ukuran tanggal di tengah atas
DATE_Y = 80             # posisi tanggal (titik tengah teks)
CLOCK_TOP = 128         # posisi atas angka jam
CLOCK_H = 190           # tinggi angka jam
CLOCK_STROKE = 0.135    # tebal garis jam (CLOCK_H x angka ini), makin kecil makin tipis

# --- Efek kaca JAM (transparansi) ------------------------------------------
CLOCK_FILL_TOP = 52     # isi putih di bagian atas angka   (makin kecil makin bening)
CLOCK_FILL_BOTTOM = 48  # isi putih di bagian bawah angka
CLOCK_LENS_ALPHA = 150  # seberapa kuat efek lensa (latar di dalam angka lebih terang)
CLOCK_LENS_BRIGHT = 1.32  # kecerahan efek lensa
CLOCK_EDGE_LIGHT = 230  # kilau tepi atas-kiri
CLOCK_OUTLINE = 95      # garis tipis di sekeliling angka
CLOCK_SHADOW = 55       # bayangan di bawah angka

# --- Gambar album (di tengah) -----------------------------------------------
COVER_SIZE = 350        # ukuran gambar album (persegi)
COVER_TOP = 350         # posisi atas gambar album
COVER_RADIUS = 26       # kelengkungan sudut
COVER_SHADOW = 120      # kekuatan bayangan (0 = tanpa bayangan)

# --- Widget musik (kotak kaca) ----------------------------------------------
WIDGET_SCALE = 1.0      # 1.0 = 620x220 px; 1.2 = 20% lebih besar, dst.
WIDGET_GAP = 37         # jarak widget dari gambar album
WIDGET_TINT = 5        # lapisan putih kaca  (makin kecil makin transparan)
WIDGET_BLUR = 3        # keburaman latar di belakang kaca
WIDGET_BRIGHT = 1.06    # kecerahan latar di belakang kaca
WIDGET_RIM = 60         # garis tepi kaca
WIDGET_SHINE = 200      # kilau tepi atas-kiri (efek kaca cair)
WIDGET_RADIUS = 44      # kelengkungan sudut
TITLE_SIZE = 31         # ukuran judul lagu (di widget)
ARTIST_SIZE = 26        # ukuran nama artis (di widget)
TIME_SIZE = 21          # ukuran waktu 0:00 / -04:03

# --- Teks tanggal di sebelah kiri -------------------------------------------
LEFT_TEXT_SIZE = 38     # ukuran 3 baris teks kiri
LEFT_TEXT_X = 96        # posisi kiri
LEFT_TEXT_Y = 520       # posisi baris pertama (titik tengah teks)
LEFT_TEXT_GAP = 46      # jarak antar baris

# --- Tombol bulat Telegram & Apple ------------------------------------------
BUTTON_RADIUS = 56      # ukuran lingkaran
BUTTON_MARGIN = 150     # jarak titik tengah lingkaran dari tepi kiri/kanan
BUTTON_Y = 976          # posisi vertikal
BUTTON_TINT = 7        # lapisan putih kaca tombol
LOGO_SIZE = 58          # ukuran logo di dalam tombol
LOGO_APPLE_PATH = "storage/cache/apple.png"   # file logo Apple (kalau ada, dipakai)
LOGO_APPLE_WHITE = True                       # True = jadikan putih; False = warna asli file
LOGO_APPLE_OFFSET_Y = -4   # geser logo Apple: minus = naik, plus = turun (piksel)

# ===========================================================================

W, H = 1920, 1080   # landscape 16:9 (seperti iPad)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _logo_apple_file(n):
    """Logo Apple dari file gambar, dipotong rapat, dipusatkan di kanvas n x n."""
    img = Image.open(LOGO_APPLE_PATH).convert("RGBA")
    alpha = img.getchannel("A")
    if alpha.getextrema() == (255, 255):          # tanpa transparansi: bentuk dari gelap-terang
        lum = img.convert("L")
        w, h = lum.size
        corners = [lum.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        alpha = ImageOps.invert(lum) if sum(corners) / 4 > 127 else lum
    box = alpha.getbbox()
    if not box:
        raise ValueError("logo kosong")
    img, alpha = img.crop(box), alpha.crop(box)
    ratio = min(n / img.width, n / img.height)
    size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    img = img.resize(size, Image.LANCZOS)
    alpha = alpha.resize(size, Image.LANCZOS)
    layer = Image.new("RGBA", size, (255, 255, 255, 0)) if LOGO_APPLE_WHITE else img
    layer.putalpha(alpha.point(lambda v: v * 240 // 255))
    out = Image.new("RGBA", (n, n), (255, 255, 255, 0))
    out.alpha_composite(layer, ((n - size[0]) // 2, (n - size[1]) // 2))
    return out


def _apple_logo(n):
    if os.path.isfile(LOGO_APPLE_PATH):
        try:
            return _logo_apple_file(n)
        except Exception as e:
            logger.warning(f"logo apple dari file gagal, pakai bawaan: {e}")
    return _logo_apple(n)

def _font(path, size):
    return ImageFont.truetype(path, size)


def _prepare_art(img):
    """Buang bar hitam atas-bawah pada thumbnail YouTube 4:3 (hqdefault)."""
    img = img.convert("RGB")
    w, h = img.size
    if 1.3 <= w / h <= 1.37:
        img = img.crop((0, int(h * 0.125), w, int(h * 0.875)))
    return img


def _cover(img, w, h):
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    left = (img.width - w) // 2
    top = (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def _square(img):
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    return img.crop((left, top, left + s, top + s))


# ---------------------------------------------------------------------------
# LATAR: foto di BG_PATH (kalau belum ada, dipakai pemandangan buatan kode)
# ---------------------------------------------------------------------------
_BG_CACHE = None


def _make_fallback():
    ys = np.arange(H)
    stops = [(0, (92, 132, 190)), (520, (214, 224, 232)), (1080, (230, 214, 190))]
    cols = np.stack(
        [np.interp(ys, [p for p, _ in stops], [c[k] for _, c in stops]) for k in range(3)], axis=1
    )
    img = Image.fromarray(np.repeat(cols[:, None, :], W, axis=1).astype("uint8"), "RGB")
    xs = np.arange(W)
    for base, amp, col, ph in ((640, 90, (96, 128, 120), 0.4), (760, 70, (62, 104, 66), 1.7),
                               (900, 60, (36, 78, 40), 3.1)):
        edge = base + amp * np.sin(xs / 310 + ph) + amp * 0.4 * np.sin(xs / 97 + ph * 2)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.polygon([(0, H)] + [(int(x), int(y)) for x, y in zip(xs[::6], edge[::6])] + [(W, H)],
                  fill=col + (255,))
        lay = lay.filter(ImageFilter.GaussianBlur(2))
        out = img.convert("RGBA")
        out.alpha_composite(lay)
        img = out.convert("RGB")
    return img


def _background():
    global _BG_CACHE
    if _BG_CACHE is None:
        if os.path.isfile(BG_PATH):
            img = _cover(Image.open(BG_PATH).convert("RGB"), W, H).filter(ImageFilter.GaussianBlur(0.8))
        else:
            img = _make_fallback()
        _BG_CACHE = ImageEnhance.Brightness(img).enhance(BG_DIM)
    return _BG_CACHE.convert("RGBA")


# ---------------------------------------------------------------------------
# MASK, KACA, TEKS
# ---------------------------------------------------------------------------
def _rounded_mask(w, h, r, scale=4):
    big = Image.new("L", (w * scale, h * scale), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        [0, 0, w * scale - 1, h * scale - 1], radius=r * scale, fill=255
    )
    return big.resize((w, h), Image.LANCZOS)


def _ellipse_mask(w, h, scale=4):
    big = Image.new("L", (w * scale, h * scale), 0)
    ImageDraw.Draw(big).ellipse([0, 0, w * scale - 1, h * scale - 1], fill=255)
    return big.resize((w, h), Image.LANCZOS)


def _ss(w, h, painter, scale=4):
    """Lapisan RGBA anti-alias: gambar di skala besar lalu diperkecil."""
    big = Image.new("RGBA", (w * scale, h * scale), (255, 255, 255, 0))
    painter(ImageDraw.Draw(big), scale)
    return big.resize((w, h), Image.LANCZOS)


def _edges(mask, d=2, rim_size=5):
    """Tepi atas-kiri (hi), bawah-kanan (lo), dan garis keliling (rim)."""
    p = 8
    w, h = mask.size
    m2 = Image.new("L", (w + 2 * p, h + 2 * p), 0)
    m2.paste(mask, (p, p))
    box = (p, p, p + w, p + h)
    hi = ImageChops.subtract(m2, ImageChops.offset(m2, d, d)).crop(box)
    lo = ImageChops.subtract(m2, ImageChops.offset(m2, -d, -d)).crop(box)
    rim = ImageChops.subtract(m2, m2.filter(ImageFilter.MinFilter(rim_size))).crop(box)
    return hi, lo, rim


def _glass(bg, box, mask, blur=22, tint=40, bright=1.15, rim_alpha=95,
           liquid=False, shine=200):
    """Panel kaca: latar di bawahnya diburamkan + lapisan putih + garis tepi.
    liquid=True menambah kilau tepi atas-kiri seperti kaca cair."""
    x0, y0, x1, y1 = box
    region = bg.crop(box).filter(ImageFilter.GaussianBlur(blur))
    region = ImageEnhance.Brightness(region).enhance(bright)
    region = Image.alpha_composite(
        region, Image.new("RGBA", region.size, (255, 255, 255, tint))
    )
    bg.paste(region, (x0, y0), mask)

    hi, lo, rim = _edges(mask)
    white = Image.new("RGBA", mask.size, (255, 255, 255, 255))
    rim = rim.point(lambda v: v * rim_alpha // 255)
    if liquid:
        hi = hi.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: min(255, v * shine // 255))
        lo = lo.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: v * 55 // 255)
        dark = Image.new("RGBA", mask.size, (0, 0, 0, 255))
        dark.putalpha(lo)
        bg.alpha_composite(dark, (x0, y0))
        white.putalpha(ImageChops.add(hi, rim))
    else:
        white.putalpha(rim)
    bg.alpha_composite(white, (x0, y0))


# ---------------------------------------------------------------------------
# JAM: angka garis tipis seragam (monoline) + efek liquid glass
# ---------------------------------------------------------------------------
def _arc(cx, cy, r, a0, a1):
    n = max(8, int(abs(a1 - a0) / 2.5))
    return [
        (cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
        for i in range(n + 1)
    ]


def _stadium(L, R_, ya, yb):
    r = (R_ - L) / 2
    cx = (L + R_) / 2
    pts = _arc(cx, ya + r, r, 180, 360) + _arc(cx, yb - r, r, 0, 180)
    return [pts + [pts[0]]]


def _digit_paths(ch, L, R_, Y0, Y1):
    """Garis tengah tiap angka (tinggi-sempit). Koordinat piksel."""
    r = (R_ - L) / 2
    cx = (L + R_) / 2
    hh = Y1 - Y0
    ym = (Y0 + Y1) / 2
    if ch == "0":
        return _stadium(L, R_, Y0, Y1)
    if ch == "1":
        return [[(L, Y0 + hh * 0.07), (R_, Y0), (R_, Y1)]]
    if ch == "2":
        top = _arc(cx, Y0 + r, r, 180, 395)
        return [top + [(L, Y1), (R_, Y1)]]
    if ch == "3":
        p = (_arc(cx, Y0 + r, r, 200, 360) + _arc(cx, ym - r, r, 0, 90)
             + _arc(cx, ym + r, r, 270, 360) + _arc(cx, Y1 - r, r, 0, 160))
        return [p, [(cx - r * 0.35, ym), (cx, ym)]]
    if ch == "4":
        yb = Y0 + hh * 0.68
        sx = R_ - r * 0.42
        return [[(sx, Y1), (sx, Y0), (L, yb), (R_, yb)]]
    if ch == "5":
        yj = Y0 + hh * 0.40
        bowl = _arc(cx, yj + r, r, 200, 360) + _arc(cx, Y1 - r, r, 0, 160)
        return [[(R_, Y0), (L, Y0), (L, yj)], bowl]
    if ch in "69":
        yb = Y0 + hh * 0.42
        stem = _arc(cx, Y0 + r, r, 290, 180) + [(L, yb + r)]
        paths = [stem] + _stadium(L, R_, yb, Y1)
        if ch == "9":
            paths = [[(L + R_ - x, Y0 + Y1 - y) for x, y in p] for p in paths]
        return paths
    if ch == "7":
        return [[(L, Y0), (R_, Y0), (cx - r * 0.1, Y1)]]
    if ch == "8":
        return _stadium(L, R_, Y0, ym) + _stadium(L, R_, ym, Y1)
    return []


def _clock_mask(text, top, height=None, S=3):
    """Mask jam (L, W x ch) dengan garis seragam, digambar 3x lalu diperkecil."""
    height = height or CLOCK_H
    c = height / 430.0
    T = max(8, round(height * CLOCK_STROKE))
    m = 40
    ch = height + 2 * m
    colon_w, gap = 68 * c, 36 * c
    widths = [colon_w if t == ":" else (104 * c if t == "1" else 172 * c) for t in text]
    total = sum(widths) + gap * (len(text) - 1)

    big = Image.new("L", (W * S, ch * S), 0)
    d = ImageDraw.Draw(big)
    rr = T * S / 2

    y0, y1 = m, m + height
    x = (W - total) / 2
    for t, w in zip(text, widths):
        if t == ":":
            cx = x + w / 2
            for fy in (0.29, 0.70):
                cy = y0 + height * fy
                rad = T * 0.56 * S
                d.ellipse([cx * S - rad, cy * S - rad, cx * S + rad, cy * S + rad], fill=255)
        else:
            for path in _digit_paths(t, x + T / 2, x + w - T / 2, y0 + T / 2, y1 - T / 2):
                pts = [(px * S, py * S) for px, py in path]
                d.line(pts, fill=255, width=int(T * S), joint="curve")
                for px, py in pts:
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=255)
        x += w + gap
    return big.resize((W, ch), Image.LANCZOS), top - m


def _glass_clock(bg, text, top):
    """Jam liquid glass: tipis, transparan, tepi terang di sisi atas-kiri."""
    mask, y = _clock_mask(text, top)
    ch = mask.height
    region = bg.crop((0, y, W, y + ch))

    shadow = Image.new("RGBA", (W, ch), (0, 0, 0, 255))
    shadow.putalpha(
        ImageChops.offset(mask.filter(ImageFilter.GaussianBlur(8)), 0, 5).point(
            lambda v: v * CLOCK_SHADOW // 255)
    )
    region = Image.alpha_composite(region, shadow)

    lens = ImageEnhance.Brightness(region.filter(ImageFilter.GaussianBlur(7))).enhance(CLOCK_LENS_BRIGHT)
    region.paste(lens, (0, 0), mask.point(lambda v: v * CLOCK_LENS_ALPHA // 255))

    span = CLOCK_FILL_TOP - CLOCK_FILL_BOTTOM
    grad = Image.linear_gradient("L").resize((W, ch)).point(
        lambda v: int(CLOCK_FILL_TOP - v * span / 255))
    white = Image.new("RGBA", (W, ch), (255, 255, 255, 255))
    white.putalpha(ImageChops.multiply(mask, grad))
    region = Image.alpha_composite(region, white)

    hi = ImageChops.subtract(mask, ImageChops.offset(mask, 2, 2)).filter(
        ImageFilter.GaussianBlur(0.6)).point(lambda v: min(255, v * CLOCK_EDGE_LIGHT // 255))
    lo = ImageChops.subtract(mask, ImageChops.offset(mask, -2, -2)).filter(
        ImageFilter.GaussianBlur(0.6)).point(lambda v: v * 70 // 255)
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(3))).point(
        lambda v: v * CLOCK_OUTLINE // 255)
    dark = Image.new("RGBA", (W, ch), (0, 0, 0, 255))
    dark.putalpha(lo)
    light = Image.new("RGBA", (W, ch), (255, 255, 255, 255))
    light.putalpha(ImageChops.add(hi, edge))
    region = Image.alpha_composite(region, dark)
    region = Image.alpha_composite(region, light)
    bg.paste(region, (0, y))


def _fit(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "...", font=font) > max_w:
        text = text[:-1]
    return text.rstrip() + "..."


# ---------------------------------------------------------------------------
# IKON (digambar vektor, anti-alias)
# ---------------------------------------------------------------------------
def _round_poly(d, pts, fill, s, w=2):
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=fill, width=int(w * s), joint="curve")


def _widget_painter():
    """Bar progres, gelombang, bintang, mundur, jeda, maju, AirPlay (dasar 620x220)."""

    def paint(d, s):
        main = (255, 255, 255, 235)
        soft = (255, 255, 255, 150)

        bx0, bx1, by = 92, 528, 118
        d.rounded_rectangle([bx0 * s, (by - 3) * s, bx1 * s, (by + 3) * s],
                            radius=3 * s, fill=(255, 255, 255, 85))
        d.rounded_rectangle([bx0 * s, (by - 3) * s, (bx0 + 34) * s, (by + 3) * s],
                            radius=3 * s, fill=(255, 255, 255, 235))

        for i, hh in enumerate([7, 15, 23, 14, 6]):
            x = 566 + i * 7
            d.rounded_rectangle([(x - 1.5) * s, (38 - hh / 2) * s, (x + 1.5) * s, (38 + hh / 2) * s],
                                radius=1.5 * s, fill=(255, 255, 255, 120))

        cy = 172
        cx = 44
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            r = 14 if i % 2 == 0 else 6
            pts.append(((cx + r * math.cos(ang)) * s, (cy + 1 + r * math.sin(ang)) * s))
        d.line(pts + [pts[0]], fill=soft, width=int(2.2 * s), joint="curve")

        cx = 205
        _round_poly(d, [((cx - 20) * s, cy * s), ((cx - 2) * s, (cy - 12) * s), ((cx - 2) * s, (cy + 12) * s)], main, s)
        _round_poly(d, [((cx - 2) * s, cy * s), ((cx + 16) * s, (cy - 12) * s), ((cx + 16) * s, (cy + 12) * s)], main, s)

        cx = 310
        for dx in (-14, 4):
            d.rounded_rectangle([(cx + dx) * s, (cy - 16) * s, (cx + dx + 10) * s, (cy + 16) * s],
                                radius=3 * s, fill=main)

        cx = 415
        _round_poly(d, [((cx + 20) * s, cy * s), ((cx + 2) * s, (cy - 12) * s), ((cx + 2) * s, (cy + 12) * s)], main, s)
        _round_poly(d, [((cx + 2) * s, cy * s), ((cx - 16) * s, (cy - 12) * s), ((cx - 16) * s, (cy + 12) * s)], main, s)

        cx = 576
        for rad in (15, 8):
            d.arc([(cx - rad) * s, (cy - 3 - rad) * s, (cx + rad) * s, (cy - 3 + rad) * s],
                  start=130, end=50, fill=soft, width=int(2.2 * s))
        _round_poly(d, [((cx - 9) * s, (cy + 14) * s), ((cx + 9) * s, (cy + 14) * s), (cx * s, (cy + 4) * s)], soft, s, 1.5)

    return paint


def _logo_telegram(n):
    def paint(d, s):
        p = lambda x, y: (x * n * s, y * n * s)
        pts = [p(.08, .47), p(.92, .14), p(.77, .85), p(.52, .66), p(.41, .80), p(.38, .62)]
        d.polygon(pts, fill=(255, 255, 255, 240))
        d.line([p(.38, .62), p(.80, .27)], fill=(255, 255, 255, 0), width=max(1, int(n * s * .035)))
    return _ss(n, n, paint)


def _logo_apple(n):
    def paint(d, s):
        k = n * s

        def circ(cx, cy, r, fill):
            d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=fill)

        on, off = (255, 255, 255, 240), (255, 255, 255, 0)
        circ(.37, .45, .24, on)
        circ(.63, .45, .24, on)
        circ(.50, .60, .30, on)
        circ(.40, .72, .20, on)
        circ(.60, .72, .20, on)
        circ(.93, .41, .18, off)                 # gigitan
        circ(.50, .26, .06, off)                 # lekuk atas
        d.polygon([(.52 * k, .22 * k), (.57 * k, .07 * k), (.71 * k, .03 * k),
                   (.66 * k, .17 * k), (.55 * k, .24 * k)], fill=on)   # daun
    return _ss(n, n, paint)


# ---------------------------------------------------------------------------
# RENDER UTAMA
# ---------------------------------------------------------------------------
def _render(thumb_path, title, artist, duration, out_path):
    now = datetime.now(TZ)
    art = _prepare_art(Image.open(thumb_path))
    bg = _background()

    # jam kaca
    if CLOCK_24H:
        clock = f"{now.hour:02d}:{now.minute:02d}"
    else:
        clock = f"{now.hour % 12 or 12}:{now.minute:02d}"
    _glass_clock(bg, clock, top=CLOCK_TOP)

    # gambar album besar di tengah (dengan bayangan lembut)
    cs = COVER_SIZE
    cx = (W - cs) // 2
    cover = _square(art).resize((cs, cs), Image.LANCZOS).convert("RGBA")
    cmask = _rounded_mask(cs, cs, COVER_RADIUS)
    if COVER_SHADOW > 0:
        pad = 60
        sh = Image.new("L", (cs + 2 * pad, cs + 2 * pad), 0)
        sh.paste(cmask.point(lambda v: v * COVER_SHADOW // 255), (pad, pad + 16))
        shadow = Image.new("RGBA", sh.size, (0, 0, 0, 255))
        shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(24)))
        bg.alpha_composite(shadow, (cx - pad, COVER_TOP - pad))
    bg.paste(cover, (cx, COVER_TOP), cmask)

    # widget musik (kaca cair), ukuran mengikuti WIDGET_SCALE
    sc = WIDGET_SCALE
    ww, wh = round(620 * sc), round(220 * sc)
    wx = (W - ww) // 2
    wy = COVER_TOP + cs + WIDGET_GAP
    _glass(bg, (wx, wy, wx + ww, wy + wh), _rounded_mask(ww, wh, round(WIDGET_RADIUS * sc)),
           blur=WIDGET_BLUR, tint=WIDGET_TINT, bright=WIDGET_BRIGHT,
           rim_alpha=WIDGET_RIM, liquid=True, shine=WIDGET_SHINE)
    painter = _widget_painter()
    bg.alpha_composite(_ss(ww, wh, lambda d, s: painter(d, s * sc)), (wx, wy))

    # dua tombol bulat: Telegram (kiri), Apple (kanan)
    r = BUTTON_RADIUS
    for ccx in (BUTTON_MARGIN, W - BUTTON_MARGIN):
        _glass(bg, (ccx - r, BUTTON_Y - r, ccx + r, BUTTON_Y + r),
               _ellipse_mask(2 * r, 2 * r), tint=BUTTON_TINT)
    bg.alpha_composite(_logo_telegram(LOGO_SIZE), (BUTTON_MARGIN - LOGO_SIZE // 2, BUTTON_Y - LOGO_SIZE // 2))
    bg.alpha_composite(_apple_logo(LOGO_SIZE), (W - BUTTON_MARGIN - LOGO_SIZE // 2, BUTTON_Y - LOGO_SIZE // 2 + LOGO_APPLE_OFFSET_Y))

    # teks
    overlay = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(overlay)
    f_brand = _font(FONT_REGULAR, BRAND_SIZE)
    f_date = _font(FONT_REGULAR, DATE_SIZE)
    f_title = _font(FONT_BOLD, round(TITLE_SIZE * sc))
    f_artist = _font(FONT_REGULAR, round(ARTIST_SIZE * sc))
    f_time = _font(FONT_REGULAR, round(TIME_SIZE * sc))
    f_left = _font(FONT_REGULAR, LEFT_TEXT_SIZE)

    d.text((BRAND_X, BRAND_Y), BRAND, font=f_brand, fill=(255, 255, 255, 235), anchor="lm")

    date_top = f"{DAYS[now.weekday()]} {MONTHS[now.month - 1]} {now.day}"
    d.text((W // 2, DATE_Y), date_top, font=f_date, fill=(255, 255, 255, 240), anchor="mm")

    title = _fit(d, str(title or "Unknown"), f_title, round(500 * sc))
    artist = _fit(d, str(artist or "Unknown"), f_artist, round(500 * sc))
    d.text((wx + ww // 2, wy + round(40 * sc)), title, font=f_title, fill=(255, 255, 255, 255), anchor="mm")
    d.text((wx + ww // 2, wy + round(80 * sc)), artist, font=f_artist, fill=(255, 255, 255, 160), anchor="mm")

    dur = str(duration or "")
    remain = f"-{dur}" if ":" in dur else "-0:00"
    d.text((wx + round(30 * sc), wy + round(118 * sc)), "0:00", font=f_time, fill=(255, 255, 255, 175), anchor="lm")
    d.text((wx + ww - round(30 * sc), wy + round(118 * sc)), remain, font=f_time, fill=(255, 255, 255, 175), anchor="rm")

    # tanggal & agenda (kolom kiri, seperti widget iPad)
    date_low = f"{DAYS[now.weekday()]}, {MONTHS[now.month - 1]} {now.day}"
    d.text((LEFT_TEXT_X, LEFT_TEXT_Y), date_low, font=f_left, fill=(255, 255, 255, 245), anchor="lm")
    d.text((LEFT_TEXT_X, LEFT_TEXT_Y + LEFT_TEXT_GAP), "No events today", font=f_left, fill=(255, 255, 255, 245), anchor="lm")
    d.text((LEFT_TEXT_X, LEFT_TEXT_Y + 2 * LEFT_TEXT_GAP), "Your day is clear", font=f_left, fill=(255, 255, 255, 140), anchor="lm")

    # garis home
    d.rounded_rectangle([(W - 360) // 2, 1054, (W + 360) // 2, 1062], radius=4, fill=(255, 255, 255, 235))
    bg.alpha_composite(overlay)

    bg.convert("RGB").save(out_path)
    return out_path


async def gen_qthumb(client, videoid):
    data = state.get(client.me.id, "GEN_THUMB")
    title = data["title"]
    duration = data["duration"]
    logger.info(f"Duration: {duration}")
    thumbnail = data["thumbnail"]
    logger.info(f"Url thumbnail: {thumbnail}")
    channel = data["channel"]

    src = f"storage/cache/thumb{videoid}.png"
    valid, _ = ButtonUtils.cek_tg(thumbnail)
    if valid:
        await Tools.bash(f"wget {thumbnail} -O {src}")
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(src, mode="wb")
                    await f.write(await resp.read())
                    await f.close()

    # jam & tanggal ikut waktu saat ini, jadi tidak di-cache
    out_path = f"storage/cache/{videoid}_lock.png"
    try:
        return await asyncio.to_thread(
            _render, src, title, channel, duration, out_path
        )
    finally:
        try:
            os.remove(src)
        except Exception:
            pass