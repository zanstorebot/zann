import io
import os
import random
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from helpers.fakex_render import EMOJI_RE, FONT_DIR, FONT_FILES, emoji_font_path

ICON_DIR = "storage/template"

# font San Francisco (file disiapkan sendiri, lisensi Apple), cadangan: Inter
SF_FONTS = {
    "regular": ("storage/cache/SFUIDisplay-Regular.ttf", "storage/cache/SFUIDisplay-Regular.otf",
                "storage/cache/SF-Pro-Display-Regular.otf", "storage/cache/fonts/SF-Pro-Display-Regular.otf"),
    "bold": ("storage/cache/SFUIDisplay-Bold.ttf", "storage/cache/SFUIDisplay-Bold.otf",
             "storage/cache/SF-Pro-Display-Bold.otf", "storage/cache/fonts/SF-Pro-Display-Bold.otf"),
}
W, H = 1179, 2556
F = W / 555                     # skala dari screenshot referensi (lebar 555px)

THEMES = {
    "dark": dict(bg="#121214", blob_in="#2C2C2E", blob_out="#0E5E52", bubble="#3B3B3D",
                 text="#FFFFFF", ts="#9A9A9F", menu="#272928", sep="#3E403F",
                 label="#FFFFFF", red="#FF453A", status="#FFFFFF", dim=(0, 0, 0, 60),
                 menu_alpha=228),
    "light": dict(bg="#EFEAE2", blob_in="#FFFFFF", blob_out="#D9FDD3", bubble="#FFFFFF",
                  text="#000000", ts="#8E8E93", menu="#F2F2F2", sep="#D1D1D6",
                  label="#000000", red="#FF3B30", status="#000000", dim=(0, 0, 0, 35),
                  menu_alpha=235),
}
MENU = [("Star", "star"), ("Reply", "reply"), ("Forward", "forward"),
        ("Copy", "copy"), ("Report", "report"), ("Delete", "delete")]


def s(v):
    """Satuan screenshot referensi -> piksel hasil."""
    return int(round(v * F))


def font_path(kind):
    """SF kalau ada, kalau tidak Inter (diunduh ensure_fonts fakex)."""
    for path in SF_FONTS[kind]:
        if os.path.exists(path):
            return path
    return f"{FONT_DIR}/{FONT_FILES[kind][0]}"


def uses_sf():
    return all(font_path(k).startswith("storage/cache/S") for k in SF_FONTS)


def _font(kind, size):
    return ImageFont.truetype(font_path(kind), s(size))


# ---------------------------------------------------------------- teks + emoji
_EMOJI = {}


def _emoji(cluster, h):
    path = emoji_font_path()
    if not path:
        return None
    key = (cluster, h)
    if key not in _EMOJI:
        canvas = Image.new("RGBA", (160, 136), (0, 0, 0, 0))
        ImageDraw.Draw(canvas).text((0, 0), cluster, font=ImageFont.truetype(path, 109), embedded_color=True)
        box = canvas.getbbox()
        em = canvas.crop(box) if box else None
        _EMOJI[key] = em.resize((int(em.width * h / em.height), h), Image.LANCZOS) if em else None
    return _EMOJI[key]


def _tokens(text, font):
    """[('t'|'e', isi, lebar)] per kata/emoji."""
    out, pos = [], 0
    eh = int(font.size * 1.05)
    for m in list(EMOJI_RE.finditer(text)) + [None]:
        chunk = text[pos:m.start()] if m else text[pos:]
        for part in re.findall(r"\S+|\s+", chunk):
            out.append(("t", part, font.getlength(part)))
        if m:
            em = _emoji(m.group(), eh)
            out.append(("e", m.group(), (em.width + s(3.5)) if em else font.getlength(m.group())))
            pos = m.end()
    return out


def _wrap(text, font, max_w):
    lines = []
    for para in text.split("\n"):
        line, w = [], 0
        for tok in _tokens(para, font):
            if tok[0] == "t" and tok[1].isspace() and not line:
                continue
            if w + tok[2] > max_w and line:
                while line and line[-1][1].isspace():
                    w -= line.pop()[2]
                lines.append((line, w)); line, w = [], 0
                if tok[1].isspace():
                    continue
            line.append(tok); w += tok[2]
        lines.append((line, w))
    return lines


def _draw_line(img, d, toks, x, y, font, color):
    asc = font.getmetrics()[0]
    for kind, val, w in toks:
        if kind == "e":
            em = _emoji(val, int(font.size * 1.05))
            if em:
                img.alpha_composite(em, (int(x), int(y + asc - em.height + font.size * 0.2)))
            else:
                d.text((x, y), val, font=font, fill=color)
        else:
            d.text((x, y), val, font=font, fill=color)
        x += w


# ---------------------------------------------------------------- latar & ikon
def _blurred_chat(T, seed):
    """Chat palsu di belakang (diblur): header, gelembung masuk/keluar, avatar."""
    rng = random.Random(seed)
    bg = Image.new("RGBA", (W, H), T["bg"])
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, W, s(110)], fill=T["blob_in"])                      # header
    d.ellipse([s(80), s(65), s(130), s(115)], fill="#9A9A9A")             # avatar header
    d.ellipse([s(40), s(305), s(110), s(375)], fill="#E0A21B")            # avatar emoji kuning
    y = s(150)
    while y < H - s(120):
        out = rng.random() < 0.55
        w = s(rng.randint(150, 390))
        h = s(rng.choice([42, 42, 60, 80]))
        x0 = W - s(18) - w if out else s(rng.choice([18, 140]))
        d.rounded_rectangle([x0, y, x0 + w, y + h], radius=s(16),
                            fill=T["blob_out"] if out else T["blob_in"])
        y += h + s(rng.randint(14, 40))
    bg = bg.filter(ImageFilter.GaussianBlur(s(14)))
    bg.alpha_composite(Image.new("RGBA", (W, H), T["dim"]))
    return bg


def _icon(name, size, color):
    src = Image.open(f"{ICON_DIR}/{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    tinted = Image.new("RGBA", src.size, color)
    tinted.putalpha(src.split()[3])
    return tinted


def _status_bar(img, d, T, now):
    f = _font("bold", 20)
    d.text((s(76), s(30)), now.strftime("%I:%M").lstrip("0"), font=f, fill=T["status"], anchor="mm")
    c = T["status"]
    # sinyal 4 batang
    for i, hgt in enumerate((5, 8, 11, 14)):
        x = s(428 + i * 7)
        d.rounded_rectangle([x, s(37 - hgt), x + s(4.5), s(37)], radius=s(1), fill=c)
    # wifi: 3 busur
    cx, cy = s(470), s(38)
    for r in (16, 11, 6):
        d.arc([cx - s(r), cy - s(r), cx + s(r), cy + s(r)], 225, 315, fill=c, width=s(2.6))
    d.ellipse([cx - s(2), cy - s(4), cx + s(2), cy], fill=c)
    # baterai
    bx, by = s(492), s(25)
    d.rounded_rectangle([bx, by, bx + s(25), by + s(12)], radius=s(3.5), outline=c, width=s(1.2))
    d.rounded_rectangle([bx + s(2), by + s(2), bx + s(20), by + s(10)], radius=s(2), fill=c)
    d.rounded_rectangle([bx + s(26), by + s(4), bx + s(27.6), by + s(8)], radius=s(1), fill=c)


# ---------------------------------------------------------------- render utama
def render_wa_ios(text, theme="dark", when=None, mark=True):
    T = THEMES.get(theme, THEMES["dark"])
    now = when or datetime.now()
    img = _blurred_chat(T, text)
    d = ImageDraw.Draw(img)

    f_text, f_ts, f_menu = _font("regular", 23.5), _font("regular", 15.5), _font("regular", 22.7)
    ts = now.strftime("%I:%M %p").lstrip("0")
    ts_w = f_ts.getlength(ts)

    # ---- bubble (lebar maks ±72% layar)
    pad_l, pad_r, pad_t, pad_b = s(15), s(14), s(10), s(9)
    max_text = s(400) - pad_l - pad_r
    lines = _wrap(text, f_text, max_text)
    line_h = s(32)
    last_w = lines[-1][1]
    ts_inline = last_w + s(10) + ts_w <= max_text
    text_w = max(max(w for _, w in lines), (last_w + s(10) + ts_w) if ts_inline else ts_w)
    bw = int(text_w + pad_l + pad_r)
    bh = int(pad_t + line_h * len(lines) + (0 if ts_inline else s(18)) + pad_b + s(4))

    menu_h = s(60.5) * len(MENU)
    gap = s(15)
    # bubble diletakkan seperti referensi (y=614), naik kalau pesan panjang
    by = min(s(614), H - s(150) - menu_h - gap - bh)
    bx = s(22)

    shape = Image.new("L", (W, H), 0)
    ds = ImageDraw.Draw(shape)
    ds.rounded_rectangle([bx, by, bx + bw, by + bh], radius=s(18), fill=255)
    # ekor kiri-bawah
    ds.polygon([(bx + s(14), by + bh - s(18)), (bx - s(10), by + bh), (bx + s(20), by + bh - s(2))], fill=255)
    shape = shape.resize((W * 2, H * 2)).filter(ImageFilter.GaussianBlur(1)).resize((W, H), Image.LANCZOS)
    img.paste(Image.new("RGBA", (W, H), T["bubble"]), (0, 0), shape)

    y = by + pad_t
    for toks, _ in lines:
        _draw_line(img, d, toks, bx + pad_l, y, f_text, T["text"])
        y += line_h
    d.text((bx + bw - pad_r, by + bh - pad_b), ts, font=f_ts, fill=T["ts"], anchor="rs")

    # ---- menu
    mx0, my0 = bx, by + bh + gap
    mx1, my1 = s(356), my0 + menu_h
    mask = Image.new("L", (W * 2, H * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([mx0 * 2, my0 * 2, mx1 * 2, my1 * 2], radius=s(26) * 2, fill=255)
    # menu agak tembus pandang: chat blur di belakang sedikit terlihat (seperti aslinya)
    menu_fill = Image.new("RGBA", (W, H), T["menu"])
    menu_fill.putalpha(mask.resize((W, H), Image.LANCZOS).point(lambda v: v * T["menu_alpha"] // 255))
    img.alpha_composite(menu_fill)
    row = s(60.5)
    icon_sz = s(31)       # PNG Phosphor punya margin, jadi dibuat lebih besar
    for i, (label, icon) in enumerate(MENU):
        ry = my0 + row * i
        color = T["red"] if icon == "delete" else T["label"]
        d.text((mx0 + s(22), ry + row / 2), label, font=f_menu, fill=color, anchor="lm")
        ic = _icon(icon, icon_sz, color)
        img.alpha_composite(ic, (int(mx1 - s(26) - icon_sz / 2), int(ry + row / 2 - icon_sz / 2)))
        if i:
            d.line([(mx0, ry), (mx1, ry)], fill=T["sep"], width=max(1, s(0.7)))

    # ---- status bar & home indicator
    _status_bar(img, d, T, now)
    d.rounded_rectangle([s(178), H - s(19), s(377), H - s(13)], radius=s(3), fill=T["status"])

    # ---- tanda parodi (kecil, samar, pojok kanan bawah)
    if mark:
        d.text((W - s(10), H - s(6)), "parodi", font=_font("regular", 9), fill=T["sep"], anchor="rd")

    out = io.BytesIO()
    img.convert("RGB").save(out, "PNG", optimize=True)
    out.name = "wa_ios.png"
    out.seek(0)
    return out
