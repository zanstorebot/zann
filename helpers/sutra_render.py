import io
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEMPLATE = "storage/template/sutra.jpg"
FONT_DIR = "storage/cache/fonts"
PILL_FONT = ("Inter-Bold.otf",
             "https://github.com/rsms/inter/raw/v3.19/docs/font-files/Inter-Bold.otf")

BASE = 400                          # ukuran template asli
HD = 2048                           # ukuran hasil
OVAL = (210.5, 188.5, 297.5, 319.5)   # kotak elips foto
PILL = (102, 153, 296, 171)         # pil putih "KONDOM IMPOR"
PILL_PAD = 9                        # jarak teks dari tepi pil
TEXT_RED = (222, 30, 38)            # merah tulisan asli
FEATHER = 0.035                     # tepi foto sedikit lembut


async def ensure_font(fetch):
    """Unduh font tulisan pil sekali ke FONT_DIR. fetch = httpx.AsyncClient (Tools.fetch)."""
    path = f"{FONT_DIR}/{PILL_FONT[0]}"
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    resp = await fetch.get(PILL_FONT[1], follow_redirects=True)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)


def _box(b, k):
    return [v * k for v in b]


def _oval_photo(raw, w, h):
    """
    Foto di-crop 'cover' sesuai rasio oval. Kanvas dibuat lebih besar dari oval
    supaya tepi blur jatuh di luar oval -> foto lama tidak kelihatan di pinggir.
    Return (gambar, padding).
    """
    f = max(2, int(min(w, h) * FEATHER))
    pad = int(f * 2.5)                 # ruang blur (supaya tidak terpotong di tepi kanvas)
    W, H = w + pad * 2, h + pad * 2
    av = Image.open(raw).convert("RGBA")
    scale = max(W / av.width, H / av.height)
    av = av.resize((max(W, round(av.width * scale)), max(H, round(av.height * scale))), Image.LANCZOS)
    left, top = (av.width - W) // 2, (av.height - H) // 3      # wajah biasanya agak ke atas
    av = av.crop((left, top, left + W, top + H))
    inset = pad - f * 0.7               # elips sedikit lebih besar dari oval asli
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([inset, inset, W - 1 - inset, H - 1 - inset], fill=255)
    av.putalpha(mask.filter(ImageFilter.GaussianBlur(f * 0.6)))
    return av, pad


def _spaced_layout(text, font, max_w):
    """Lebar huruf + jarak antar huruf ala 'K O N D O M'. Return (spasi, total_lebar)."""
    widths = [font.getlength(c) for c in text]
    gaps = max(1, len(text) - 1)
    size = font.size
    for ratio in (0.55, 0.45, 0.35, 0.25, 0.15, 0.08):
        sp = size * ratio
        total = sum(widths) + sp * gaps
        if total <= max_w:
            return sp, total, widths
    return size * 0.08, sum(widths) + size * 0.08 * gaps, widths


def _draw_pill(img, text, k):
    x0, y0, x1, y1 = _box(PILL, k)
    d = ImageDraw.Draw(img)
    # tutup tulisan lama dengan pil putih baru
    d.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, fill="white")

    path = f"{FONT_DIR}/{PILL_FONT[0]}"
    max_w = (x1 - x0) - PILL_PAD * 2 * k
    size = int((y1 - y0) * 0.78)
    while size > 6:
        font = ImageFont.truetype(path, size)
        sp, total, widths = _spaced_layout(text, font, max_w)
        if total <= max_w:
            break
        size -= 1
    asc, desc = font.getmetrics()
    cap = font.getbbox("H")
    cy = (y0 + y1) / 2
    y = cy - (cap[1] + cap[3]) / 2
    x = (x0 + x1) / 2 - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=TEXT_RED)
        x += w + sp


def render_sutra(avatar, text=None, size=HD):
    k = size / BASE
    img = Image.open(TEMPLATE).convert("RGBA").resize((size, size), Image.LANCZOS)
    # template asli kecil (400px) -> sedikit dipertajam setelah diperbesar
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

    if text:
        _draw_pill(img, text.upper(), k)

    if avatar:
        x0, y0, x1, y1 = _box(OVAL, k)
        w, h = round(x1 - x0), round(y1 - y0)
        photo, pad = _oval_photo(avatar, w, h)
        img.alpha_composite(photo, (round(x0) - pad, round(y0) - pad))

    out = io.BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=95, subsampling=0)
    out.name = "sutra.jpg"
    out.seek(0)
    return out
