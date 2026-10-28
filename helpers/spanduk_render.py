import io
import math
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

TEMPLATE = "storage/template/spanduk.jpg"
FONT_DIR = "storage/cache/fonts"
FONT_CUSTOM = "spanduk.ttf"     # taruh font sendiri dengan nama ini -> dipakai paling dulu
FONTS = (                       # (nama file, [url]) dicoba berurutan sampai ada yang berhasil
    ("Ultra.ttf", ("https://github.com/google/fonts/raw/main/apache/ultra/Ultra-Regular.ttf",
                   "https://github.com/google/fonts/raw/main/ofl/ultra/Ultra-Regular.ttf")),
    ("AlfaSlabOne.ttf", ("https://github.com/google/fonts/raw/main/ofl/alfaslabone/AlfaSlabOne-Regular.ttf",)),
)

BASE = (1200, 675)              # ukuran foto spanduk asli
SCALE = 2                       # hasil 2400 x 1350

# --- judul lama (area yang dihapus) ---------------------------------
OLD_L, OLD_R = (130, 275), (1100, 252.5)    # garis tengah judul lama, naik ke kanan
BAND_X = (106, 1148)
BAND_UP, BAND_DOWN = 31, 30

# --- judul baru ------------------------------------------------------
TEXT_CX, TEXT_CY = 625, 264     # tengahnya
TITLE_ANGLE = 0.5              # sudut kemiringannha
FADE = 0.20                     # pudar atau fadenya
CAP_H = 42                      # tinggi hurufnya
MAX_W = 1030                    # lebar maksimum judul

OUTLINE_W = 2.2                 # garis tepi gelap
OUTLINE = (104, 58, 48)
EXTRUDE = (118, 106, 78)        # bayangan tebal di kanan-bawah huruf
EXTRUDE_OFF = (2.0, 5.0)
# gradasi warna huruf dari atas ke bawah (diambil dari piksel judul asli)
STOPS = ((0.00, (232, 72, 60)), (0.35, (233, 82, 64)), (0.50, (228, 100, 66)),
         (0.62, (240, 150, 84)), (0.75, (241, 196, 104)), (0.90, (238, 214, 118)),
         (1.00, (232, 205, 108)))
SHADE_REF = 232.0               # kecerahan latar putih spanduk asli

# --- ruang kosong di sekitar judul (supaya tidak menabrak) -----------
BORDER = (130, 243, -0.0257)    # tepi bawah garis kuning atas: x, y, kemiringan
OBSTACLES = ((165, 235, 303),   # kepala bebek
             (780, 840, 303),   # kepala angsa
             (955, 1020, 296))  # jengger ayam: (x awal, x akhir, y batas bawah)
FLOOR = 310                     # batas bawah di tempat lain (huruf MENTHOK dst.)


def _font_path():
    paths = [f"{FONT_DIR}/{FONT_CUSTOM}"] + [f"{FONT_DIR}/{n}" for n, _ in FONTS]
    return next((p for p in paths if os.path.exists(p) and os.path.getsize(p) > 10_000), None)


async def ensure_font(fetch):
    """Unduh font judul sekali ke FONT_DIR. fetch = httpx.AsyncClient (Tools.fetch)."""
    if _font_path():
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, urls in FONTS:
        for url in urls:
            try:
                resp = await fetch.get(url, follow_redirects=True)
                resp.raise_for_status()
                with open(f"{FONT_DIR}/{name}", "wb") as f:
                    f.write(resp.content)
                return
            except Exception:
                continue
    raise RuntimeError(f"Font gagal diunduh. Taruh font .ttf sendiri di {FONT_DIR}/{FONT_CUSTOM}")


def _old_center_y(x):
    return OLD_L[1] + (x - OLD_L[0]) * (OLD_R[1] - OLD_L[1]) / (OLD_R[0] - OLD_L[0])


def _smooth_median(arr, win):
    """Median bergeser sepanjang kolom: buang benda yang ikut terambil (kepala bebek, jengger)."""
    pad = win // 2
    ext = np.pad(arr, ((pad, pad), (0, 0)), mode="edge")
    view = np.lib.stride_tricks.sliding_window_view(ext, win, axis=0)
    return np.median(view, axis=-1)


def _erase_title(img, S):
    """Hapus judul lama: latar diisi dari tepi atas-bawah per kolom (ikut terang spanduk)."""
    a = np.asarray(img, np.float32).copy()
    xs = np.arange(int(BAND_X[0] * S), int(BAND_X[1] * S))
    cy = _old_center_y(xs / S) * S
    top = np.round(cy - BAND_UP * S).astype(int)
    bot = np.round(cy + BAND_DOWN * S).astype(int)
    m = 3 * S
    ref_t = np.stack([a[t - m:t - 1, x].mean(0) for x, t in zip(xs, top)])
    ref_b = np.stack([a[b + 2:b + 2 + m, x].mean(0) for x, b in zip(xs, bot)])
    bad = ref_t[:, 2] < ref_b[:, 2] - 20          # tepi atas kena garis kuning -> pakai warna bawah
    ref_t[bad] = ref_b[bad]
    win = 101 * S | 1
    ref_t, ref_b = _smooth_median(ref_t, win), _smooth_median(ref_b, win)
    rng = np.random.default_rng()
    feather = 2 * S
    for j, x in enumerate(xs):
        t, b = top[j], bot[j]
        n = b - t + 1
        w = np.linspace(0, 1, n)[:, None]
        fill = ref_t[j] * (1 - w) + ref_b[j] * w + rng.normal(0, 1.5, (n, 3))
        alpha = np.ones((n, 1), np.float32)
        alpha[:feather] = np.linspace(0.5, 1, feather)[:, None]
        alpha[-feather:] = np.linspace(1, 0.5, feather)[:, None]
        a[t:b + 1, x] = a[t:b + 1, x] * (1 - alpha) + fill * alpha
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _gradient(h, y_top, y_bot):
    """Gradasi merah -> oranye -> kuning dari atas ke bawah huruf."""
    t = np.clip((np.arange(h) - y_top) / max(1, y_bot - y_top), 0, 1)
    pos = [p for p, _ in STOPS]
    cols = np.array([c for _, c in STOPS], np.float32)
    return np.stack([np.interp(t, pos, cols[:, i]) for i in range(3)], axis=-1).astype(np.float32)


def _title_layer(text, S, k=1.0):
    """Judul bertepi + bayangan tebal + gradasi, sudah dimiringkan.
    k = pengecil tinggi huruf. Hasil: (layer RGBA, setengah lebar, tinggi ke atas, tinggi ke bawah)
    dalam satuan piksel foto asli."""
    path = _font_path()
    probe = ImageFont.truetype(path, 200)
    size = 200 * CAP_H * k * S / -probe.getbbox("H", anchor="ls")[1]
    ow = max(1, int(round(OUTLINE_W * S)))
    font = ImageFont.truetype(path, int(size))
    width = font.getlength(text) + 2 * (ow + EXTRUDE_OFF[0] * S)
    if width > MAX_W * S:                      # judul panjang -> huruf mengecil, tetap muat
        size *= MAX_W * S / width
        font = ImageFont.truetype(path, int(size))
    cap = -font.getbbox("H", anchor="ls")[1]
    pad = int(12 * S)
    cw, ch = int(font.getlength(text)) + pad * 2, int(cap * 2.2) + pad * 2
    base = ch // 2 + cap // 2                  # tengah huruf = tengah kanvas -> putar pas di tengah

    def mask(stroke=0):
        m = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(m).text((pad, base), text, font=font, fill=255, anchor="ls",
                               stroke_width=stroke, stroke_fill=255)
        return m

    fill_m, edge_m = mask(), mask(ow)
    ext_m = Image.new("L", (cw, ch), 0)        # bayangan tebal = tepi digeser bertahap ke kanan-bawah
    steps = max(2, int(EXTRUDE_OFF[1] * S))
    for i in range(steps + 1):
        dx, dy = round(EXTRUDE_OFF[0] * S * i / steps), round(EXTRUDE_OFF[1] * S * i / steps)
        ext_m = ImageChops.lighter(ext_m, ImageChops.offset(edge_m, dx, dy))

    edge_a = np.asarray(edge_m, np.float32)[..., None] / 255.0
    fill_a = np.asarray(fill_m, np.float32)[..., None] / 255.0
    grain = 1 + np.random.default_rng().normal(0, 0.025, (ch, cw, 1))   # bintik cat spanduk
    rgb = np.empty((ch, cw, 3), np.float32)
    rgb[:] = EXTRUDE
    rgb = rgb * (1 - edge_a) + np.array(OUTLINE, np.float32) * edge_a
    rgb = rgb * (1 - fill_a) + _gradient(ch, base - cap, base)[:, None, :] * grain * fill_a
    alpha = np.asarray(ext_m, np.float32)[..., None]
    layer = Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), alpha], -1).astype(np.uint8), "RGBA")
    layer = layer.rotate(-TITLE_ANGLE, resample=Image.BICUBIC, expand=True)
    half_w = (font.getlength(text) / 2 + ow) / S
    up = (cap / 2 + ow) / S
    return layer, half_w, up, up + EXTRUDE_OFF[1]


def _free_space(x):
    """Batas atas (garis kuning) dan batas bawah (kepala bebek, angsa, jengger) di kolom x."""
    top = BORDER[1] + BORDER[2] * (x - BORDER[0]) + 3
    bottom = next((y for a, b, y in OBSTACLES if a <= x <= b), FLOOR)
    return top, bottom


def _fit_center(half_w, up, down):
    """Tinggi tengah judul yang tidak menabrak garis kuning/gambar; None kalau tidak muat."""
    t = math.tan(math.radians(TITLE_ANGLE))
    lo, hi = -1e9, 1e9
    for x in np.linspace(TEXT_CX - half_w, TEXT_CX + half_w, 33):
        top, bottom = _free_space(x)
        lo = max(lo, top + up - t * (x - TEXT_CX))
        hi = min(hi, bottom - down - t * (x - TEXT_CX))
    return None if lo > hi else min(max(TEXT_CY, lo), hi)


def render_spanduk(text, scale=SCALE):
    S = scale
    text = " ".join(text.upper().split())
    base_img = Image.open(TEMPLATE).convert("RGB").resize((BASE[0] * S, BASE[1] * S), Image.LANCZOS)
    img = _erase_title(base_img, S)

    k = 1.0
    for _ in range(10):                        # judul terlalu besar untuk ruang miring -> kecilkan sedikit
        layer, half_w, up, down = _title_layer(text, S, k)
        cy = _fit_center(half_w, up, down)
        if cy is not None:
            break
        k *= 0.94
    cy = TEXT_CY if cy is None else cy

    full = Image.new("RGBA", img.size, (0, 0, 0, 0))
    full.paste(layer, (int(TEXT_CX * S) - layer.width // 2, int(cy * S) - layer.height // 2))

    # pencahayaan: huruf ikut terang-gelap latar; lalu dipudarkan seperti tulisan bawah
    gray = np.asarray(img.convert("L").filter(ImageFilter.GaussianBlur(30 * S)), np.float32)
    shade = np.clip(gray / SHADE_REF, 0.78, 1.08)[..., None]
    arr = np.asarray(full, np.float32)
    arr[..., :3] = np.clip(arr[..., :3] * shade, 0, 255)
    arr[..., 3] *= 1 - FADE
    soft = Image.fromarray(arr.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(0.55 * S))
    out = img.convert("RGBA")
    out.alpha_composite(soft)

    res = np.asarray(out.convert("RGB"), np.float32)
    res += np.random.default_rng().normal(0, 1.4, res.shape)           # grain kamera
    buf = io.BytesIO()
    Image.fromarray(np.clip(res, 0, 255).astype(np.uint8)).save(buf, "JPEG", quality=93, subsampling=0)
    buf.name = "spanduk.jpg"
    buf.seek(0)
    return buf
