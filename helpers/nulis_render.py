import io
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEMPLATE = "storage/template/kertas.jpg"
FONT_DIR = "storage/cache/fonts"
FONT_CUSTOM = "nulis.ttf"   # taruh font sendiri dengan nama ini -> dipakai paling dulu
_RAW = "https://github.com/google/fonts/raw/main/ofl"
FONTS = (                   # (nama file, url) dicoba berurutan sampai ada yang berhasil
    ("Caveat.ttf", f"{_RAW}/caveat/Caveat%5Bwght%5D.ttf"),
    ("ReenieBeanie.ttf", f"{_RAW}/reeniebeanie/ReenieBeanie.ttf"),
    ("IndieFlower.ttf", f"{_RAW}/indieflower/IndieFlower-Regular.ttf"),
)

BASE = (415, 738)           # ukuran foto kertas asli
SCALE = 3                   # hasil 1245 x 2214
LINES = 24
# ujung kiri & kanan tiap garis kertas di foto (hasil ukur piksel)
ENDS = (
    ((81, 209), (335, 187)), ((82, 226), (337, 204)), ((82, 242), (338, 221)), ((82, 259), (340, 238)),
    ((83, 276), (341, 255)), ((84, 292), (343, 272)), ((84, 309), (345, 290)), ((84, 326), (346, 308)),
    ((86, 343), (347, 325)), ((85, 361), (349, 343)), ((85, 378), (351, 361)), ((86, 396), (352, 379)),
    ((86, 414), (354, 398)), ((86, 432), (356, 417)), ((86, 450), (358, 436)), ((87, 468), (359, 455)),
    ((87, 487), (361, 475)), ((88, 506), (363, 494)), ((88, 525), (365, 514)), ((88, 544), (367, 534)),
    ((88, 564), (369, 555)), ((89, 583), (370, 575)), ((89, 603), (372, 596)), ((90, 623), (374, 617)),
)
USE = (0.05, 0.97)          # bagian garis yang dipakai menulis (kiri, kanan)
PITCH = 18                  # jarak antar garis di bidang datar
FLAT_W = 250                # lebar bidang datar (perbandingan ke PITCH)
MARGIN = 14                 # ruang lebih di atas/bawah bidang supaya huruf tidak terpotong
INK = (35, 70, 200)         # tinta pulpen biru, dikali warna kertas (multiply)
BASELINE = 1.2              # tulisan duduk tepat di atas garis


def _font_paths():
    paths = [f"{FONT_DIR}/{FONT_CUSTOM}"] + [f"{FONT_DIR}/{n}" for n, _ in FONTS]
    return [p for p in paths if os.path.exists(p) and os.path.getsize(p) > 10_000]


async def ensure_font(fetch):
    """Unduh font tulisan tangan sekali ke FONT_DIR. fetch = httpx.AsyncClient (Tools.fetch)."""
    if _font_paths():
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, url in FONTS:
        try:
            resp = await fetch.get(url, follow_redirects=True)
            resp.raise_for_status()
            with open(f"{FONT_DIR}/{name}", "wb") as f:
                f.write(resp.content)
            return
        except Exception:
            continue
    raise RuntimeError(f"Font gagal diunduh. Taruh font .ttf sendiri di {FONT_DIR}/{FONT_CUSTOM}")


def _homography(S):
    """Pas-kan bidang datar <-> foto dari 48 ujung garis, lalu beri koefisien PERSPECTIVE PIL
    (piksel foto berskala S -> piksel kanvas datar berskala S)."""
    A, b = [], []
    for k, (l, r) in enumerate(ENDS):
        for u, t in ((0, USE[0]), (FLAT_W, USE[1])):
            x, y = l[0] + (r[0] - l[0]) * t, l[1] + (r[1] - l[1]) * t
            v = k * PITCH
            A += [[u, v, 1, 0, 0, 0, -u * x, -v * x], [0, 0, 0, u, v, 1, -u * y, -v * y]]
            b += [x, y]
    c = np.linalg.lstsq(np.array(A, float), np.array(b, float), rcond=None)[0]
    flat_to_photo = np.append(c, 1.0).reshape(3, 3)
    to_canvas = np.array([[S, 0, 0], [0, S, MARGIN * S], [0, 0, 1]], float)
    from_photo = np.diag([1 / S, 1 / S, 1.0])
    m = to_canvas @ np.linalg.inv(flat_to_photo) @ from_photo
    return (m / m[2, 2]).flatten()[:8].tolist()


def _wrap(text, measure, max_w):
    """Bungkus per kata; kata yang terlalu panjang dipecah per huruf."""
    out = []
    for para in text.replace("\r", "").split("\n"):
        cur = ""
        for word in para.split():
            while measure(word) > max_w:
                n = max(1, len(word) - 1)
                while n > 1 and measure(word[:n]) > max_w:
                    n -= 1
                if cur:
                    out.append(cur)
                    cur = ""
                out.append(word[:n])
                word = word[n:]
            trial = f"{cur} {word}".strip()
            if cur and measure(trial) > max_w:
                out.append(cur)
                cur = word
            else:
                cur = trial
        out.append(cur)
    return out


def _glyph(ch, font, rot, shear):
    """Satu huruf: putar sedikit + miring ke kanan seperti tulisan tangan."""
    pad = font.size
    base = pad * 2
    tile = Image.new("L", (int(font.getlength(ch)) + pad * 2, pad * 3), 0)
    ImageDraw.Draw(tile).text((pad, base), ch, font=font, fill=255, anchor="ls")
    tile = tile.rotate(rot, resample=Image.BICUBIC, center=(pad, base))
    tile = tile.transform(tile.size, Image.AFFINE, (1, shear, -shear * base, 0, 1, 0), Image.BICUBIC)
    return tile, pad, base


def _paint_text(text, rng, S):
    """Tulis teks di bidang datar (mask tinta 0..1), tiap huruf dibuat sedikit berbeda."""
    path = _font_paths()[0]
    probe = ImageFont.truetype(path, 100)
    asc = -probe.getbbox("l", anchor="ls")[1]
    size = int(100 * (PITCH * S * 0.98) / asc)
    fonts = {f: ImageFont.truetype(path, max(8, int(size * f))) for f in (0.94, 0.97, 1.0, 1.03, 1.06)}
    main = fonts[1.0]
    max_w = (FLAT_W - 8) * S
    keys = list(fonts)
    lines = _wrap(text, lambda t: main.getlength(t) * 1.03 + size * 0.015 * len(t), max_w)
    if len(lines) > LINES - 1:
        raise ValueError(f"Teks terlalu panjang, muat sekitar {LINES - 1} baris ({len(lines)} baris dibutuhkan).")

    cw, ch = FLAT_W * S, (PITCH * (LINES - 1) + MARGIN * 2) * S
    canvas = Image.new("L", (cw, ch), 0)
    for r, line in enumerate(lines):
        x = (3 + rng.uniform(-1.5, 1.5)) * S
        drift = rng.uniform(-0.7, 0.7) * S
        tilt = rng.uniform(-0.010, 0.010)
        phase, freq = rng.uniform(0, 6.28), rng.uniform(0.012, 0.03) / S
        x0 = x
        for c in line:
            f = fonts[rng.choice(keys)]
            if c == " ":
                x += size * rng.uniform(0.26, 0.42)
                continue
            by = (MARGIN + (r + 1) * PITCH - BASELINE) * S + drift + tilt * (x - x0)
            by += math.sin(x * freq + phase) * 0.6 * S + rng.uniform(-0.55, 0.55) * S
            tile, pad, base = _glyph(c, f, rng.uniform(-3.5, 3.5), rng.uniform(0.10, 0.20))
            canvas.paste(255, (int(x - pad), int(by - base)), tile)
            x += f.getlength(c) * rng.uniform(0.96, 1.05) + size * 0.015
    a = np.asarray(canvas, np.float32) / 255.0
    return a * _pressure(rng, ch, cw)


def _pressure(rng, h, w):
    """Tekanan pulpen tidak rata: ada bagian tinta yang lebih tipis/pucat."""
    g = np.random.default_rng(rng.randint(0, 2**31))
    coarse = (g.random((max(2, h // 40), max(2, w // 40))) * 255).astype(np.uint8)
    field = np.asarray(Image.fromarray(coarse).resize((w, h), Image.BICUBIC), np.float32) / 255.0
    return 0.80 + 0.30 * field


def render_nulis(text, scale=SCALE):
    S = scale
    rng = random.Random()
    ow, oh = BASE[0] * S, BASE[1] * S
    paper = Image.open(TEMPLATE).convert("RGB").resize((ow, oh), Image.LANCZOS)

    ink = _paint_text(text, rng, S)
    layer = Image.fromarray((np.clip(ink, 0, 1) * 255).astype(np.uint8))
    layer = layer.transform((ow, oh), Image.PERSPECTIVE, _homography(S), Image.BICUBIC)
    layer = layer.filter(ImageFilter.GaussianBlur(0.5 * S))   # selembut foto aslinya

    # multiply: tinta ikut gelap-terang, tekstur, dan bayangan kertas
    a = np.asarray(layer, np.float32)[..., None] / 255.0
    p = np.asarray(paper, np.float32)
    out = p * (1 - a + a * np.array(INK, np.float32) / 255.0)
    out += np.random.default_rng().normal(0, 1.6, out.shape)   # grain kamera
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=94, subsampling=0)
    buf.name = "nulis.jpg"
    buf.seek(0)
    return buf
