import io
import math
import os
import random
import re
import unicodedata
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "storage/cache/fonts"
FONT_FILES = {
    "regular": ("Inter-Regular.otf", "https://github.com/rsms/inter/raw/v3.19/docs/font-files/Inter-Regular.otf"),
    "bold": ("Inter-Bold.otf", "https://github.com/rsms/inter/raw/v3.19/docs/font-files/Inter-Bold.otf"),
}
# font utama: San Francisco (file disiapkan sendiri di storage/cache), cadangan Inter
SF_FONTS = {
    "regular": ("storage/cache/SFUIDisplay-Regular.ttf", "storage/cache/SFUIDisplay-Regular.otf"),
    "bold": ("storage/cache/SFUIDisplay-Bold.ttf", "storage/cache/SFUIDisplay-Bold.otf"),
}


def font_path(kind):
    """'regular' / 'bold' -> SFUIDisplay kalau ada, kalau tidak Inter."""
    for path in SF_FONTS[kind]:
        if os.path.exists(path):
            return path
    return f"{FONT_DIR}/{FONT_FILES[kind][0]}"


# emoji berwarna: pakai font sistem (paket fonts-noto-color-emoji), kalau tidak ada diunduh
EMOJI_SYSTEM = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
EMOJI_FILE = ("NotoColorEmoji.ttf",
              "https://github.com/googlefonts/noto-emoji/raw/v2.051/fonts/NotoColorEmoji.ttf")

# cadangan untuk huruf yang tidak ada di Inter (huruf hias, simbol, aksara lain)
FALLBACK_FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf",
)


def emoji_font_path():
    local = f"{FONT_DIR}/{EMOJI_FILE[0]}"
    for path in (EMOJI_SYSTEM, local):
        if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
            return path
    return None


async def _download(fetch, url, path, min_size):
    if os.path.exists(path) and os.path.getsize(path) > min_size:
        return
    resp = await fetch.get(url, follow_redirects=True)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)


async def ensure_fonts(fetch):
    """Unduh font Inter (+ emoji kalau sistem tidak punya) sekali ke FONT_DIR."""
    os.makedirs(FONT_DIR, exist_ok=True)
    for fname, url in FONT_FILES.values():
        await _download(fetch, url, f"{FONT_DIR}/{fname}", 10_000)
    if not emoji_font_path():
        await _download(fetch, EMOJI_FILE[1], f"{FONT_DIR}/{EMOJI_FILE[0]}", 1_000_000)


# satuan layout = piksel screenshot X mobile.
# Digambar S kali (supersampling), lalu diperkecil OUT kali -> garis/ikon halus, tidak pecah.
S = 3.5
OUT = 0.5          # hasil akhir ±1260px lebar (batas aman foto Telegram 1280)

# palet resmi tampilan X
THEMES = {
    "light": dict(bg="#FFFFFF", text="#0F1419", sub="#536471", line="#EFF3F4", link="#1D9BF0"),
    "dim": dict(bg="#15202B", text="#F7F9F9", sub="#8B98A5", line="#38444D", link="#1D9BF0"),
    "dark": dict(bg="#000000", text="#E7E9EA", sub="#71767B", line="#2F3336", link="#1D9BF0"),
}
BLUE = "#1D9BF0"

# satu "grapheme" emoji: bendera, ZWJ sequence, skin tone, variation selector
EMOJI_RE = re.compile(
    r"(?:[\U0001F1E6-\U0001F1FF]{2})"
    r"|(?:[\U0001F300-\U0001FAFF\u2600-\u27BF\u2300-\u23FF\u2B00-\u2BFF\u3030\u303D\u3297\u3299\u00A9\u00AE\u203C\u2049\u2122\u2139\u2194-\u21AA]"
    r"[\uFE0F\U0001F3FB-\U0001F3FF]*"
    r"(?:\u200D[\U0001F300-\U0001FAFF\u2600-\u27BF][\uFE0F\U0001F3FB-\U0001F3FF]*)*)"
)
HIGHLIGHT_RE = re.compile(r"^(?:[#@$]\w+|https?://\S+|\w+\.(?:com|id|net|org|io|me)\S*)")


def px(v):
    return int(round(v * S))


def human(n):
    """Format angka ala X: 999, 1.2K, 12K, 1.2M."""
    if n < 1000:
        return str(n)
    for div, suf in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if n >= div:
            v = n / div
            return (f"{v:.1f}".rstrip("0").rstrip(".") if v < 10 else f"{int(v)}") + suf
    return str(n)


class Fonts:
    def __init__(self):
        reg_path, bold_path = font_path("regular"), font_path("bold")
        self.reg = lambda size: ImageFont.truetype(reg_path, px(size))
        self.bold = lambda size: ImageFont.truetype(bold_path, px(size))
        path = emoji_font_path()
        self.emoji = ImageFont.truetype(path, 109) if path else None  # CBDT hanya ukuran 109
        self.fallback = [p for p in FALLBACK_FONTS if os.path.exists(p)]
        self._fb_cache = {}

    def fallback_for(self, ch, size_px):
        """Font cadangan pertama yang punya glyph ch (None = tidak ada)."""
        for path in self.fallback:
            key = (path, size_px)
            if key not in self._fb_cache:
                self._fb_cache[key] = ImageFont.truetype(path, size_px)
            if has_glyph(self._fb_cache[key], ch):
                return self._fb_cache[key]
        return None


_GLYPH_CACHE = {}


def _glyph_print(font, ch):
    """Sidik glyph: bbox + piksel hasil gambar (untuk dibandingkan dengan kotak notdef)."""
    box = font.getbbox(ch)
    w, h = max(1, box[2] - box[0]), max(1, box[3] - box[1])
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((-box[0], -box[1]), ch, font=font, fill=255)
    return box, im.tobytes()


def has_glyph(font, ch):
    """True kalau font punya glyph ch (tidak sama dengan kotak 'notdef')."""
    if ch.isspace():
        return True
    key = (font.path, font.size, ch)
    if key not in _GLYPH_CACHE:
        nk = (font.path, font.size, None)
        if nk not in _GLYPH_CACHE:
            _GLYPH_CACHE[nk] = _glyph_print(font, "\U0010FFFD")
        _GLYPH_CACHE[key] = _glyph_print(font, ch) != _GLYPH_CACHE[nk]
    return _GLYPH_CACHE[key]


# ---------------------------------------------------------------- teks + emoji
def split_runs(text):
    """[('t', 'halo '), ('e', '😂'), ...]"""
    runs, pos = [], 0
    for m in EMOJI_RE.finditer(text):
        if m.start() > pos:
            runs.append(("t", text[pos:m.start()]))
        runs.append(("e", m.group()))
        pos = m.end()
    if pos < len(text):
        runs.append(("t", text[pos:]))
    return runs


_EMOJI_CACHE = {}


def emoji_img(fonts, cluster, size):
    if not fonts.emoji:
        return None
    key = (cluster, size)
    if key in _EMOJI_CACHE:
        return _EMOJI_CACHE[key]
    canvas = Image.new("RGBA", (160, 136), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).text((0, 0), cluster, font=fonts.emoji, embedded_color=True)
    box = canvas.getbbox()
    if not box:
        return None
    em = canvas.crop(box)
    h = px(size * 1.12)
    em = em.resize((max(1, int(em.width * h / em.height)), h), Image.LANCZOS)
    _EMOJI_CACHE[key] = em
    return em


def token_width(fonts, font, kind, value, size):
    if kind == "e":
        em = emoji_img(fonts, value, size)
        # lebar asli emoji + jarak tipis (bendera lebih lebar dari emoji biasa)
        return em.width + px(size * 0.14) if em else font.getlength(value)
    return font.getlength(value)


def _glyph_split(fonts, font, word):
    """Pisah kata: bagian yang ada di Inter tetap 't', sisanya ('f', ch, font cadangan).
    Huruf yang tidak ada di font mana pun dibuang (daripada jadi kotak)."""
    if all(has_glyph(font, ch) for ch in word):
        return [("t", word)]
    out, buf = [], ""
    for ch in word:
        if has_glyph(font, ch):
            buf += ch
            continue
        # huruf hias (𝓐 𝐀 Ａ ...) -> huruf biasa padanannya
        plain = unicodedata.normalize("NFKC", ch)
        if plain != ch and all(has_glyph(font, c) for c in plain):
            buf += plain
            continue
        if buf:
            out.append(("t", buf)); buf = ""
        fb = fonts.fallback_for(ch, font.size)
        if fb:
            out.append(("f", ch, fb))
    if buf:
        out.append(("t", buf))
    return out


def layout_text(fonts, font, text, max_w, size):
    """Bungkus teks per kata (emoji = satu token). Return list baris berisi token."""
    lines = []
    for para in text.split("\n"):
        tokens = []
        for kind, val in split_runs(para):
            if kind == "e":
                tokens.append(("e", val))
            else:
                for w in re.findall(r"\S+|\s+", val):
                    tokens += _glyph_split(fonts, font, w)
        line, width = [], 0
        for tok in tokens:
            kind, val = tok[0], tok[1]
            if kind == "f":
                w = tok[2].getlength(val)
                if width + w > max_w and line:
                    lines.append(line); line, width = [], 0
                line.append(("f", val, w, tok[2])); width += w
                continue
            w = token_width(fonts, font, kind, val, size)
            if kind == "t" and val.isspace():
                if line:
                    line.append((kind, val, w)); width += w
                continue
            if width + w > max_w and line:
                while line and line[-1][0] == "t" and line[-1][1].isspace():
                    width -= line.pop()[2]
                lines.append(line); line, width = [], 0
            # kata lebih panjang dari 1 baris -> potong per huruf
            if kind == "t" and w > max_w:
                chunk = ""
                for ch in val:
                    if font.getlength(chunk + ch) > max_w:
                        lines.append([("t", chunk, font.getlength(chunk))]); chunk = ""
                    chunk += ch
                val, w = chunk, font.getlength(chunk)
            line.append((kind, val, w)); width += w
        lines.append(line)
    return lines


def draw_tokens(img, draw, fonts, font, tokens, x, y, size, color, link_color=None):
    """Gambar satu baris token. y = top baris."""
    asc = font.getmetrics()[0]
    for tok in tokens:
        kind, val, w = tok[:3]
        if kind == "f":  # huruf dari font cadangan, baseline disamakan
            fb = tok[3]
            draw.text((x, y + asc - fb.getmetrics()[0]), val, font=fb, fill=color)
            x += w
            continue
        if kind == "e":
            em = emoji_img(fonts, val, size)
            if em:
                img.alpha_composite(em, (int(x + px(size * 0.07)), int(y + asc - em.height + px(size * 0.18))))
            else:
                draw.text((x, y), val, font=font, fill=color)
        else:
            c = link_color if link_color and HIGHLIGHT_RE.match(val) else color
            draw.text((x, y), val, font=font, fill=c)
        x += w
    return x


def truncate(fonts, font, text, max_w, size):
    toks = layout_text(fonts, font, text.replace("\n", " "), 10**9, size)[0]
    out, w = [], 0
    ell = font.getlength("…")
    for t in toks:
        if w + t[2] > max_w - ell:
            out.append(("t", "…", ell)); break
        out.append(t); w += t[2]
    return out


# ---------------------------------------------------------------- ikon vektor
def _stroke(draw, pts, color, w):
    draw.line(pts, fill=color, width=w, joint="curve")


def icon_reply(d, x, y, s, c, w):
    # gelembung chat dengan ekor kiri-bawah
    r = s * 0.42
    cx, cy = x + s * 0.5, y + s * 0.45
    pts = [(cx + r * math.cos(t), cy + r * 0.86 * math.sin(t))
           for t in [math.radians(a) for a in range(120, 470, 10)]]
    pts += [(x + s * 0.18, y + s * 0.92), (cx - r * math.cos(math.radians(60)) + s * 0.02, cy + r * 0.86 * math.sin(math.radians(120)))]
    _stroke(d, pts, c, w)


def icon_repost(d, x, y, s, c, w):
    a = s * 0.16
    # panah kiri: naik lalu ke kanan
    _stroke(d, [(x + s * 0.18, y + s * 0.82), (x + s * 0.18, y + s * 0.22), (x + s * 0.62, y + s * 0.22)], c, w)
    _stroke(d, [(x + s * 0.18 - a, y + s * 0.22 + a), (x + s * 0.18, y + s * 0.22 - a * 0.1), (x + s * 0.18 + a, y + s * 0.22 + a)], c, w)
    # panah kanan: turun lalu ke kiri
    _stroke(d, [(x + s * 0.82, y + s * 0.18), (x + s * 0.82, y + s * 0.78), (x + s * 0.38, y + s * 0.78)], c, w)
    _stroke(d, [(x + s * 0.82 - a, y + s * 0.78 - a), (x + s * 0.82, y + s * 0.78 + a * 0.1), (x + s * 0.82 + a, y + s * 0.78 - a)], c, w)


def icon_like(d, x, y, s, c, w, filled=False):
    pts = []
    for i in range(0, 361, 6):
        t = math.radians(i)
        hx = 16 * math.sin(t) ** 3
        hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x + s * 0.5 + hx * s / 36, y + s * 0.47 - hy * s / 36))
    if filled:
        d.polygon(pts, fill=c)
    _stroke(d, pts, c, w)


def icon_bookmark(d, x, y, s, c, w):
    _stroke(d, [(x + s * 0.24, y + s * 0.9), (x + s * 0.24, y + s * 0.16), (x + s * 0.76, y + s * 0.16),
                (x + s * 0.76, y + s * 0.9), (x + s * 0.5, y + s * 0.7), (x + s * 0.24, y + s * 0.9)], c, w)


def icon_share(d, x, y, s, c, w):
    _stroke(d, [(x + s * 0.5, y + s * 0.66), (x + s * 0.5, y + s * 0.1)], c, w)
    _stroke(d, [(x + s * 0.3, y + s * 0.3), (x + s * 0.5, y + s * 0.1), (x + s * 0.7, y + s * 0.3)], c, w)
    _stroke(d, [(x + s * 0.16, y + s * 0.5), (x + s * 0.16, y + s * 0.88), (x + s * 0.84, y + s * 0.88), (x + s * 0.84, y + s * 0.5)], c, w)


def icon_more(d, x, y, s, c):
    r = s * 0.075
    for i in (0.2, 0.5, 0.8):
        cx, cy = x + s * i, y + s * 0.5
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)


def verified_badge(size, color=BLUE):
    """Lencana centang X: rosette bergelombang + centang putih."""
    big = size * 4
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, R = big / 2, big * 0.47
    pts = [(c + R * (1 - 0.075 * (1 - math.cos(8 * t))) * math.cos(t),
            c + R * (1 - 0.075 * (1 - math.cos(8 * t))) * math.sin(t))
           for t in [i * math.pi / 180 for i in range(0, 360, 2)]]
    d.polygon(pts, fill=color)
    d.line([(big * 0.3, big * 0.52), (big * 0.44, big * 0.65), (big * 0.71, big * 0.37)],
           fill="white", width=int(big * 0.09), joint="curve")
    return img.resize((size, size), Image.LANCZOS)


def icon_views(d, x, y, s, c, w):
    # grafik batang: 4 batang naik
    base = y + s * 0.86
    for i, top in enumerate((0.62, 0.30, 0.48, 0.12)):
        bx = x + s * (0.16 + i * 0.23)
        d.line([(bx, base), (bx, y + s * top)], fill=c, width=w)


def x_logo(size, fg="white", bg="black"):
    """Logo X: garis '\\' tebal berongga + garis '/' tipis."""
    big = size * 6
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    P = lambda pts: [(big * a, big * b) for a, b in pts]
    d.line(P([(0.93, 0.03), (0.07, 0.97)]), fill=fg, width=int(big * 0.085))
    d.polygon(P([(0.0, 0.0), (0.32, 0.0), (1.0, 1.0), (0.68, 1.0)]), fill=fg)
    d.polygon(P([(0.10, 0.065), (0.285, 0.065), (0.90, 0.935), (0.715, 0.935)]), fill=bg)
    return img.resize((size, size), Image.LANCZOS)


def x_badge(size, border=None):
    """Lencana afiliasi X: kotak hitam sudut membulat berisi logo X putih."""
    big = size * 4
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * 0.22), fill="black",
                        outline=border, width=int(big * 0.06) if border else 0)
    logo = x_logo(int(big * 0.58), "white", "black")
    img.alpha_composite(logo, ((big - logo.width) // 2, (big - logo.height) // 2))
    return img.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------- avatar/media
def circle_avatar(raw, size, name):
    if raw:
        try:
            av = Image.open(raw).convert("RGBA")
            side = min(av.size)
            av = av.crop(((av.width - side) // 2, (av.height - side) // 2,
                          (av.width + side) // 2, (av.height + side) // 2)).resize((size, size), Image.LANCZOS)
        except Exception:
            raw = None
    if not raw:  # tanpa foto: lingkaran warna + inisial
        av = Image.new("RGBA", (size, size), random.Random(name).choice(
            ["#1D9BF0", "#F91880", "#7856FF", "#FF7A00", "#00BA7C", "#FFD400"]))
        d = ImageDraw.Draw(av)
        f = ImageFont.truetype(font_path("bold"), int(size * 0.45))
        # huruf pertama yang ada di Inter (emoji/bendera/huruf hias dilewati)
        ch = next((c for c in name if c.isalnum() and has_glyph(f, c)), "?").upper()
        d.text((size / 2, size / 2), ch, font=f, fill="white", anchor="mm")
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * 4, size * 4], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(av, (0, 0), mask.resize((size, size), Image.LANCZOS))
    return out


def rounded_media(raw, width, line_color, radius):
    img = Image.open(raw).convert("RGBA")
    h = int(img.height * width / img.width)
    h = min(h, int(width * 1.25))  # X memotong media yang terlalu tinggi
    img = img.resize((width, int(img.height * width / img.width)), Image.LANCZOS).crop((0, 0, width, h))
    mask = Image.new("L", (width, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, width - 1, h - 1], radius=radius, fill=255)
    out = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, width - 1, h - 1], radius=radius, outline=line_color, width=max(1, int(S)))
    return out


# ---------------------------------------------------------------- render utama
BULAN = ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des")


def format_waktu(when):
    """06:05 am · 31 Jul 2026"""
    return f"{when.strftime('%I:%M %p').lower()} · {when.day} {BULAN[when.month - 1]} {when.year}"


def render_fake_post(name, handle, text, avatar=None, media=None, theme="light",
                     verified=False, xbadge=True, stats=None, when=None, mark=True):
    T = THEMES.get(theme, THEMES["light"])
    F = Fonts()
    W, M = 720, 36                    # lebar total & margin luar (satuan layout)
    AV = 64                           # diameter avatar
    CX = M + AV + 14                  # awal kolom isi
    col_w = px(W - CX - M)
    rng = random.Random(f"{handle}{text}")
    when = when or datetime.now()

    if stats is None:
        views = rng.randint(3_000, 2_500_000)
        likes = int(views * rng.uniform(0.008, 0.05))
        stats = dict(views=views, likes=likes, reposts=int(likes * rng.uniform(0.05, 0.25)),
                     replies=int(likes * rng.uniform(0.03, 0.12)))

    f_name, f_sub = F.bold(26), F.reg(26)
    f_text, f_meta, f_cnt = F.reg(27), F.reg(22), F.reg(21)
    lines = layout_text(F, f_text, text, col_w, 27)
    LH = px(37)

    media_img = None
    if media:
        try:
            media_img = rounded_media(media, col_w, T["line"], px(16))
        except Exception:
            media_img = None

    # ---- tinggi isi
    y_text = px(M + 40)
    h = y_text + LH * len(lines)
    if media_img:
        h += px(14) + media_img.height
    h += px(14) + px(26)              # waktu & tanggal
    h += px(20) + px(28) + px(M)      # baris aksi + margin bawah
    # gambar terlalu pipih -> tinggikan & isi diletakkan di tengah (rasio maks 2.4 : 1)
    H = max(h, int(px(W) / 2.4))
    off = (H - h) // 2

    img = Image.new("RGBA", (px(W), H), T["bg"])
    d = ImageDraw.Draw(img)

    # ---- avatar
    img.alpha_composite(circle_avatar(avatar, px(AV), name), (px(M), off + px(M - 4)))

    # ---- baris nama: Nama [centang] [logo X] @handle            ···
    x, y_name = px(CX), off + px(M - 2)
    right_lim = px(W - M - 40)
    badges_w = (px(30) if verified else 0) + (px(30) if xbadge else 0)
    name_toks = truncate(F, f_name, name, (right_lim - x) * 0.6 - badges_w, 26)
    x = draw_tokens(img, d, F, f_name, name_toks, x, y_name, 26, T["text"])
    mid = y_name + f_name.getmetrics()[0] * 0.62
    if verified:
        b = verified_badge(px(25))
        img.alpha_composite(b, (int(x + px(5)), int(mid - b.height / 2)))
        x += px(5) + b.width
    if xbadge:
        b = x_badge(px(24), border=T["line"] if theme != "light" else None)
        img.alpha_composite(b, (int(x + px(6)), int(mid - b.height / 2)))
        x += px(6) + b.width
    meta = truncate(F, f_sub, f"@{handle}", right_lim - x - px(10), 26)
    draw_tokens(img, d, F, f_sub, meta, x + px(10), y_name, 26, T["sub"])
    icon_more(d, px(W - M - 30), off + px(M - 1), px(28), T["sub"])

    # ---- isi teks
    y = off + y_text
    for toks in lines:
        draw_tokens(img, d, F, f_text, toks, px(CX), y, 27, T["text"], T["link"])
        y += LH

    # ---- media
    if media_img:
        y += px(14)
        img.alpha_composite(media_img, (px(CX), y))
        y += media_img.height

    # ---- waktu & tanggal
    y += px(14)
    d.text((px(CX), y), format_waktu(when), font=f_meta, fill=T["sub"])
    y += px(26)

    # ---- baris aksi: reply, repost, like, views ... bookmark, share
    y += px(20)
    s_icon, sw = px(25), px(2.1)
    step = (W - CX - M - 90) / 4
    for i, (fn, n) in enumerate(((icon_reply, stats["replies"]), (icon_repost, stats["reposts"]),
                                 (icon_like, stats["likes"]), (icon_views, stats["views"]))):
        ix = px(CX - 4 + i * step)
        fn(d, ix, y, s_icon, T["sub"], sw)
        if n:
            d.text((ix + s_icon + px(9), y + s_icon / 2), human(n), font=f_cnt, fill=T["sub"], anchor="lm")
    icon_bookmark(d, px(W - M - 72), y, s_icon, T["sub"], sw)
    icon_share(d, px(W - M - 26), y, s_icon, T["sub"], sw)

    # ---- tanda parodi (kecil, pojok kanan bawah)
    if mark:
        d.text((px(W - 14), H - px(12)), "@alicedevscodes", font=F.reg(13), fill=T["line"], anchor="rd")

    # supersampling -> perkecil dengan LANCZOS: semua garis jadi halus
    final = img.convert("RGB").resize((int(img.width * OUT), int(img.height * OUT)), Image.LANCZOS)
    out = io.BytesIO()
    final.save(out, "PNG", optimize=True)
    out.name = "fakex.png"
    out.seek(0)
    return out
