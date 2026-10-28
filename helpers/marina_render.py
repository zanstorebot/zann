import io
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEMPLATE = "storage/template/marina.png"
FONT_DIR = "storage/cache/fonts"
LOGO_FONT = ("Pacifico-Regular.ttf",
             "https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf")

BASE = 800                      # ukuran template asli
HD = 2048                       # ukuran hasil (foto HD Telegram)
LOGO_ERASE = (294, 322, 486, 382)   # area logo "Marina" yang dihapus
LOGO_BOX = (302, 329, 478, 375)     # area teks pengganti (tinggi huruf logo asli)
LOGO_COLOR = (88, 45, 127)          # ungu logo asli (median piksel logo)
FLOWER = (409, 495, 74)             # tengah lingkaran pink (bunga + ceri) + jari-jari foto


async def ensure_font(fetch):
    """Unduh font logo sekali ke FONT_DIR. fetch = httpx.AsyncClient (Tools.fetch)."""
    path = f"{FONT_DIR}/{LOGO_FONT[0]}"
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    resp = await fetch.get(LOGO_FONT[1], follow_redirects=True)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)


def _box(b, k):
    return tuple(int(round(v * k)) for v in b)


def _erase(img, box):
    """Hapus area dengan isian halus dari 4 sisi (Coons patch) -> latar botol tetap natural."""
    x0, y0, x1, y1 = box
    a = np.asarray(img).astype(np.float32)
    top, bot = a[y0, x0:x1], a[y1, x0:x1]
    left, right = a[y0:y1, x0], a[y0:y1, x1]
    h, w = y1 - y0, x1 - x0
    u = np.linspace(0, 1, w)[None, :, None]
    v = np.linspace(0, 1, h)[:, None, None]
    c00, c10, c01, c11 = a[y0, x0], a[y0, x1], a[y1, x0], a[y1, x1]
    patch = ((1 - v) * top[None] + v * bot[None] + (1 - u) * left[:, None] + u * right[:, None]
             - ((1 - u) * (1 - v) * c00 + u * (1 - v) * c10 + (1 - u) * v * c01 + u * v * c11))
    a[y0:y1, x0:x1] = np.clip(patch, 0, 255)
    return Image.fromarray(a.astype(np.uint8), img.mode)


def _draw_logo(img, text, k):
    """Teks pengganti logo, ukuran otomatis menyesuaikan kotak logo asli."""
    x0, y0, x1, y1 = _box(LOGO_BOX, k)
    box_w, box_h = x1 - x0, y1 - y0
    path = f"{FONT_DIR}/{LOGO_FONT[0]}"
    size = int(box_h * 1.6)
    while size > 10:
        font = ImageFont.truetype(path, size)
        l, t, r, b = font.getbbox(text)
        if r - l <= box_w and b - t <= box_h:
            break
        size -= 2
    l, t, r, b = font.getbbox(text)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pos = (cx - (l + r) / 2, cy - (t + b) / 2)

    # bayangan tipis seperti logo asli, lalu teks utama
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    off = max(1, int(1.2 * k))
    d.text((pos[0] + off, pos[1] + off), text, font=font, fill=(50, 20, 80, 110))
    layer = layer.filter(ImageFilter.GaussianBlur(1.2 * k))
    ImageDraw.Draw(layer).text(pos, text, font=font, fill=LOGO_COLOR + (255,))
    img.alpha_composite(layer)


FEATHER = 0.045   # lebar tepi lembut, proporsi dari diameter foto (makin besar makin blur)


def _avatar_disc(raw, size):
    """Foto profil bulat dengan tepi lembut (sedikit blur) supaya menyatu dengan botol."""
    av = Image.open(raw).convert("RGBA")
    side = min(av.size)
    av = av.crop(((av.width - side) // 2, (av.height - side) // 2,
                  (av.width + side) // 2, (av.height + side) // 2)).resize((size, size), Image.LANCZOS)
    # lingkaran sedikit masuk ke dalam lalu di-blur -> tepi memudar halus, tidak terpotong
    f = max(2, int(size * FEATHER))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([f, f, size - 1 - f, size - 1 - f], fill=255)
    av.putalpha(mask.filter(ImageFilter.GaussianBlur(f * 0.6)))
    return av


def _shadow(size, k):
    """Bayangan lembut di bawah foto supaya terlihat menempel di botol."""
    pad = int(12 * k)
    sh = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pad, pad + int(2 * k), pad + size, pad + size + int(2 * k)],
                               fill=(90, 0, 40, 70))
    return sh.filter(ImageFilter.GaussianBlur(5 * k)), pad


def render_marina(avatar, text=None, size=HD):
    k = size / BASE
    img = Image.open(TEMPLATE).convert("RGBA").resize((size, size), Image.LANCZOS)

    if text:
        img = _erase(img, _box(LOGO_ERASE, k))
        _draw_logo(img, text, k)

    if avatar:
        fx, fy, fr = FLOWER
        d = int(fr * 2 * k)
        x, y = int(fx * k - d / 2), int(fy * k - d / 2)
        sh, pad = _shadow(d, k)
        img.alpha_composite(sh, (x - pad, y - pad))
        img.alpha_composite(_avatar_disc(avatar, d), (x, y))

    # template transparan -> latar putih (foto Telegram tidak mendukung transparan)
    bg = Image.new("RGB", img.size, "white")
    bg.paste(img, mask=img.split()[3])
    out = io.BytesIO()
    bg.save(out, "JPEG", quality=95, subsampling=0)
    out.name = "marina.jpg"
    out.seek(0)
    return out
