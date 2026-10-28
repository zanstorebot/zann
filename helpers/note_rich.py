"""
CARA PAKAI NOTES TABLE & EMOJI PREM !
credits: @alixedevscodes
ngaku ngaku pelernya pecah

==========================================================================
Cara pake table
==========================================================================
<heading 1>{emo:5220195537520711716|⚡} Scan QEIS ini</heading>
Halo <b>{name}</b> <emo id="5229003072335782160">👋</emo>, silakan pilih metode:

<table striped compact>
<cell h>💰 Payment</cell><cell h center>Status</cell>
<cell>QRIS</cell><cell center>✅</cell>
<cell>Dana</cell><cell center>✅</cell>
<cell colspan=2 center>Sea bank sedang <i>maintenance</i></cell>
</table>

<divider>
<quote expandable>Pembayaran diproses maksimal 5 menit setelah bukti dikirim.</quote>
<details title="Syarat & Ketentuan">
Saldo tidak bisa dikembalikan.
</details>

[Qris|cb_qris|success, emo="6156658206601906188"]
[Dana|cb_dana|primary][Gopay|cb_gopay|primary]
[Admin|https://t.me/username][Back|cb_main|danger]

==========================================================================
Tanpa table
==========================================================================
Teks biasa           -> paragraf. Baris kosong = paragraf baru.
<paragraph>..</paragraph>   atau  <p>..</p>     paragraf eksplisit
<heading>..</heading>       atau  <h>..</h>     judul (default ukuran 2)
<heading 1>..</heading>     ukuran 1 (terbesar) s/d <heading 6> (terkecil)
<divider>            atau  <hr>                 garis pemisah
<quote>..</quote>                               kutipan
<quote expandable>..</quote>                    kutipan yang bisa dibuka-tutup
<details title="Judul">..</details>             bagian lipat (tertutup)
<details title="Judul" open>..</details>        bagian lipat (terbuka)
    -> isi <details> boleh berisi blok lain (tabel, paragraf, dll)

==========================================================================
Table opsi
==========================================================================
<table [opsi]>
<cell>A1</cell><cell>B1</cell>      <- sel di baris yang SAMA = satu baris tabel
<cell>A2</cell><cell>B2</cell>      <- ganti baris (enter) = baris tabel baru
</table>

Opsi <table> 
    (tanpa opsi)   tabel dengan border  (default)
    striped        baris belang selang-seling
    compact        jarak sel lebih rapat
    plain          tanpa border  (alias: noborder)
    contoh: <table striped compact>

Opsi <cell> 
    h              sel header / judul kolom   (alias: header, th)
    left | center | right       rata horizontal
    top | middle | bottom       rata vertikal
    colspan=N      sel melebar N kolom
    rowspan=N      sel memanjang N baris
    contoh: <cell h center>Status</cell>
            <cell colspan=2 center middle>Gabung 2 kolom</cell>


==========================================================================
Format teks tebal mjinrg 
==========================================================================
<b>tebal</b>  <i>miring</i>  <u>garis bawah</u>  <s>coret</s>
<code>kode</code>  <pre>blok kode</pre>  <mark>stabilo</mark>
<sub>bawah</sub>  <sup>atas</sup>  <spoiler>rahasia</spoiler>
<a href="https://...">link</a>     (juga tg://, mailto:, tel:)
<br>                               pindah baris
Alias: <strong>=<b>  <em>=<i>  <ins>=<u>  <strike>/<del>=<s>

==========================================================================
Pake emoji prem
==========================================================================
{emo:ID}                 emoji premium (cadangan ✨)
{emo:ID|⚡}              emoji premium dengan emoji cadangan sendiri
<emo id="ID">⚡</emo>    sama seperti di atas  (alias tag: <emoji>, <tg-emoji>)

{mention}  nama yang bisa diklik      {name}  nama        {id}    user id
{day}      Senin..Minggu              {date}  tanggal     {month} Januari..
{year}     tahun                      {time}  jam:menit (WIB)
User = orang yang di-reply > lawan chat (private) > pengirim command.

==========================================================================
Pake button/tomblo
==========================================================================
[Teks|data]
[Teks|data|style]
[Teks|data|style, emo="ID"]

style : primary (biru) | success (hijau) | danger (merah)   (opsional)
emo   : ID emoji premium di depan teks tombol               (opsional)


==========================================================================
"""


import html as _html
import re
from datetime import datetime, timedelta, timezone

STYLES = ("primary", "success", "danger")
MAX_ROW = 8
DEFAULT_EMOJI = "✨"
HARI = ("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu")
BULAN = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember")

_BTN_RE = re.compile(r"\[\[?([^\[\]|\n]+)\|([^\[\]\n]+)\]\]?")
_EMO_ATTR = re.compile(r"""(?:emo|emoji|icon)\s*=\s*["']?(\d{5,})["']?""", re.I)
_EMO_SPLIT = re.compile(r"\s*,\s*(?=(?:emo|emoji|icon)\s*=)", re.I)
_BLOCK_RE = re.compile(
    r"<(paragraph|p|heading|h|quote|details|table)(\s[^>]*)?>(.*?)</\1\s*>"
    r"|<(?:divider|hr)\b[^>]*/?>",
    re.I | re.S,
)
_STRAY_RE = re.compile(
    r"</?(?:paragraph|heading|quote|details|table|cell)\b[^>]*>|</?(?:p|h)\s*>", re.I
)
_RICH_HINT = re.compile(
    r"<\s*/?\s*(?:paragraph|p|heading|h|quote|details|table|cell|divider|hr|emo|emoji|tg-emoji)\b"
    r"|\{emo:\d",
    re.I,
)
_CELL_RE = re.compile(r"<cell(\s[^>]*)?>(.*?)</cell\s*>", re.I | re.S)
_EMO_TAG_RE = re.compile(
    r"<(?:emo|emoji|tg-emoji)\b([^>]*)>(.*?)</(?:emo|emoji|tg-emoji)\s*>", re.I | re.S
)
_TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w-]*)([^<>]*)>")
_HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
_OK_HREF = re.compile(r"(?i)^(https?://|tg://|mailto:|tel:)")
_PH_RE = re.compile(r"\{(\w+)(?::([^{}]*))?\}")
_ALLOWED = {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
            "code", "pre", "mark", "sub", "sup", "tg-spoiler"}
_ALIAS = {"spoiler": "tg-spoiler"}


# ---------------------------------------------------------------------------
# Tombol
# ---------------------------------------------------------------------------
def _parse_button(label, rest):
    label = label.strip()
    data, _, extra = rest.partition("|")
    if not extra and _EMO_SPLIT.search(data):
        data, extra = _EMO_SPLIT.split(data, 1)
    data = data.strip()
    if not label or not data:
        return None, False
    style = emo = None
    same = False
    for tok in (t.strip() for t in extra.split(",")):
        if not tok:
            continue
        if tok.lower() in STYLES:
            style = tok.lower()
        else:
            m = _EMO_ATTR.fullmatch(tok)
            if m:
                emo = m.group(1)
            else:
                same = True  # "same" / penanda lain = sebaris (aturan lama)
    if re.match(r"(?i)(https?://|tg://)", data):
        kind = "url"
    elif re.match(r"(?i)t\.me/", data):
        kind, data = "url", "https://" + data
    else:
        kind = "callback"
    return {"text": label, "kind": kind, "data": data, "style": style, "emo": emo}, same


def _extract_buttons(text):
    """Pisahkan tombol dari teks. Return (teks_bersih, rows)."""
    rows, out = [], []
    for line in text.split("\n"):
        found = list(_BTN_RE.finditer(line))
        if not found:
            out.append(line)
            continue
        cur = []
        for m in found:
            btn, same = _parse_button(m.group(1), m.group(2))
            if btn is None:
                continue
            if same and not cur and rows:
                rows[-1].append(btn)
            else:
                cur.append(btn)
        if cur:
            rows.append(cur)
        rest = _BTN_RE.sub("", line)
        if rest.strip():
            out.append(rest)
    chunked = []
    for row in rows:
        for i in range(0, len(row), MAX_ROW):
            chunked.append(row[i:i + MAX_ROW])
    return "\n".join(out), chunked


extract_buttons = _extract_buttons  # dipakai helpers/buttons.py


def _btn_label(b):
    label = _html.escape(b["text"], quote=False)
    if b["emo"]:
        label = f'<tg-emoji emoji-id="{b["emo"]}">{DEFAULT_EMOJI}</tg-emoji> {label}'
    return label


def buttons_html(rows):
    """Tombol di dalam bubble: <tg-button-row><tg-button ...>."""
    out = []
    for row in rows:
        parts = []
        for b in row:
            if b["kind"] == "url":
                attrs = ['type="url"', f'url="{_html.escape(b["data"], quote=True)}"']
            else:
                attrs = ['type="callback_data"', f'data="{_html.escape(b["data"], quote=True)}"']
            if b["style"]:
                attrs.append(f'style="{b["style"]}"')
            parts.append(f'<tg-button {" ".join(attrs)}>{_btn_label(b)}</tg-button>')
        out.append(f'<tg-button-row align="center">{"".join(parts)}</tg-button-row>')
    return "".join(out)


def rows_to_markup(rows):
    """Tombol di luar bubble (inline keyboard biasa). Butuh pyrogram fork."""
    from pyrogram.enums import ButtonStyle
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    styles = {"primary": ButtonStyle.PRIMARY, "success": ButtonStyle.SUCCESS,
              "danger": ButtonStyle.DANGER}
    keyboard = []
    for row in rows:
        line = []
        for b in row:
            kw = {"text": b["text"], "style": styles.get(b["style"], ButtonStyle.DEFAULT)}
            if b["emo"]:
                kw["icon_custom_emoji_id"] = b["emo"]
            kw["url" if b["kind"] == "url" else "callback_data"] = b["data"]
            line.append(InlineKeyboardButton(**kw))
        keyboard.append(line)
    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------------
# Teks inline
# ---------------------------------------------------------------------------
def _emoji_html(emoji_id, fallback_escaped):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback_escaped or DEFAULT_EMOJI}</tg-emoji>'


def _user_name(user):
    name = " ".join(filter(None, [getattr(user, "first_name", None),
                                  getattr(user, "last_name", None)]))
    return name or getattr(user, "title", None) or "User"


def _placeholder(m, ctx):
    key, arg = m.group(1).lower(), m.group(2)
    if key == "emo" and arg:
        eid, _, fb = arg.partition("|")
        eid = eid.strip()
        if eid.isdigit() and len(eid) >= 5:
            return _emoji_html(eid, fb.strip())  # fb sudah ter-escape
        return m.group(0)
    now, user = ctx["now"], ctx.get("user")
    if key == "day":
        return HARI[now.weekday()]
    if key == "date":
        return str(now.day)
    if key == "month":
        return BULAN[now.month - 1]
    if key == "year":
        return str(now.year)
    if key == "time":
        return now.strftime("%H:%M")
    if user is not None and key in ("mention", "name", "id"):
        uid = getattr(user, "id", None)
        name = _html.escape(_user_name(user), quote=False)
        if key == "id" and uid is not None:
            return str(uid)
        if key == "name":
            return name
        if key == "mention" and uid is not None:
            return f'<a href="tg://user?id={uid}">{name}</a>'
    return m.group(0)


def _text(seg, ctx, keep_nl=False):
    if not seg:
        return ""
    s = _html.escape(seg, quote=False)
    s = _PH_RE.sub(lambda m: _placeholder(m, ctx), s)
    return s if keep_nl else s.replace("\n", "<br/>")


def _close(stack, name, out):
    if name not in stack:
        return
    while stack:
        t = stack.pop()
        out.append(f"</{t}>")
        if t == name:
            break


def _inline(s, ctx):
    holders = []

    def keep_emoji(m):
        mid = re.search(r"(\d{5,})", m.group(1))
        if not mid:
            return m.group(2)
        fb = _html.escape(m.group(2).strip() or DEFAULT_EMOJI, quote=False)
        holders.append(_emoji_html(mid.group(1), fb))
        return f"\x00{len(holders) - 1}\x00"

    s = _EMO_TAG_RE.sub(keep_emoji, s)
    out, stack, pos = [], [], 0
    for m in _TAG_RE.finditer(s):
        out.append(_text(s[pos:m.start()], ctx, keep_nl="pre" in stack))
        pos = m.end()
        closing, name, attrs = m.group(1), m.group(2).lower(), m.group(3)
        name = _ALIAS.get(name, name)
        if name == "br":
            out.append("<br/>")
        elif name in _ALLOWED:
            if closing:
                _close(stack, name, out)
            else:
                stack.append(name)
                out.append(f"<{name}>")
        elif name == "a":
            if closing:
                _close(stack, "a", out)
            else:
                h = _HREF_RE.search(attrs)
                if h and _OK_HREF.match(h.group(1)):
                    stack.append("a")
                    out.append(f'<a href="{_html.escape(h.group(1), quote=True)}">')
        else:
            out.append(_html.escape(m.group(0), quote=False))
    out.append(_text(s[pos:], ctx, keep_nl="pre" in stack))
    while stack:
        out.append(f"</{stack.pop()}>")
    res = "".join(out)
    return re.sub(r"\x00(\d+)\x00", lambda m: holders[int(m.group(1))], res)


# ---------------------------------------------------------------------------
# Blok
# ---------------------------------------------------------------------------
def _cell(attrs, text, ctx):
    a = attrs.lower()
    tag = "th" if re.search(r"\b(?:h|header|th)\b", a) else "td"
    extra = []
    for key in ("left", "center", "right"):
        if re.search(rf"\b{key}\b", a):
            extra.append(f'align="{key}"')
    for key in ("top", "middle", "bottom"):
        if re.search(rf"\b{key}\b", a):
            extra.append(f'valign="{key}"')
    for key in ("colspan", "rowspan"):
        m = re.search(rf"{key}\s*=\s*[\"']?(\d+)", a)
        if m:
            extra.append(f'{key}="{m.group(1)}"')
    sp = (" " + " ".join(extra)) if extra else ""
    return f"<{tag}{sp}>{_inline(text.strip(), ctx)}</{tag}>"


def _table(attrs, inner, ctx):
    flags = set(re.findall(r"[a-z]+", (attrs or "").lower()))
    tattrs = []
    if not ({"plain", "noborder"} & flags):
        tattrs.append("bordered")
    if "striped" in flags:
        tattrs.append("striped")
    if "compact" in flags:
        tattrs.append("compact")
    rows, cur, prev_end = [], [], 0
    for m in _CELL_RE.finditer(inner):
        if cur and "\n" in inner[prev_end:m.start()]:
            rows.append(cur)
            cur = []
        cur.append(_cell(m.group(1) or "", m.group(2), ctx))
        prev_end = m.end()
    if cur:
        rows.append(cur)
    if not rows:
        return ""
    body = "".join(f"<tr>{''.join(r)}</tr>" for r in rows)
    sp = (" " + " ".join(tattrs)) if tattrs else ""
    return f"<table{sp}>{body}</table>"


def _loose(s, ctx):
    s = _STRAY_RE.sub("", s)
    out = []
    for chunk in re.split(r"\n\s*\n", s):
        chunk = chunk.strip()
        if chunk:
            out.append(f"<p>{_inline(chunk, ctx)}</p>")
    return "".join(out)


def _block(m, ctx):
    tag = m.group(1).lower()
    attrs = m.group(2) or ""
    inner = m.group(3)
    low = attrs.lower()
    if tag in ("paragraph", "p"):
        return f"<p>{_inline(inner.strip(), ctx)}</p>"
    if tag in ("heading", "h"):
        lv = re.search(r"\b([1-6])\b", low)
        n = lv.group(1) if lv else "2"
        return f"<h{n}>{_inline(inner.strip(), ctx)}</h{n}>"
    if tag == "quote":
        exp = " expandable" if re.search(r"\bexpandable\b", low) else ""
        return f"<blockquote{exp}>{_inline(inner.strip(), ctx)}</blockquote>"
    if tag == "details":
        t = re.search(r"""title\s*=\s*(?:"([^"]*)"|'([^']*)')""", attrs, re.I)
        title = (t.group(1) or t.group(2)) if t else "Detail"
        op = " open" if re.search(r"\bopen\b", low) else ""
        return (f"<details{op}><summary>{_inline(title, ctx)}</summary>"
                f"{_blocks(inner, ctx)}</details>")
    return _table(attrs, inner, ctx)  # table


def _blocks(text, ctx):
    out, pos = [], 0
    for m in _BLOCK_RE.finditer(text):
        out.append(_loose(text[pos:m.start()], ctx))
        out.append("<hr/>" if m.group(1) is None else _block(m, ctx))
        pos = m.end()
    out.append(_loose(text[pos:], ctx))
    return "".join(out)


# ---------------------------------------------------------------------------
# API publik
# ---------------------------------------------------------------------------
class Rendered:
    def __init__(self, html, rows, warnings):
        self.html = html          # isi tanpa tombol
        self.rows = rows          # baris tombol (list of list of dict)
        self.warnings = warnings

    @property
    def full_html(self):
        """Isi + tombol di dalam bubble."""
        return self.html + buttons_html(self.rows)


def has_rich_markup(text):
    """True kalau note memakai fitur baru (tag blok, emoji premium, tombol bergaya)."""
    if not text:
        return False
    if _RICH_HINT.search(text):
        return True
    _, rows = _extract_buttons(text)
    return any(b["style"] or b["emo"] for row in rows for b in row)


def render_note(text, user=None, now=None):
    now = now or datetime.now(timezone(timedelta(hours=7)))  # WIB
    ctx = {"user": user, "now": now}
    clean, rows = _extract_buttons(text or "")
    body = _blocks(clean, ctx) or "<p>👇</p>"
    warnings = [
        f"Tombol '{b['text']}': callback_data lebih dari 64 byte"
        for row in rows for b in row
        if b["kind"] == "callback" and len(b["data"].encode()) > 64
    ]
    return Rendered(body, rows, warnings)


def only_url_rows(rows):
    """True kalau semua tombol berupa link (bisa dikirim langsung dari akun userbot)."""
    return bool(rows) and all(b["kind"] == "url" for row in rows for b in row)


def html_to_text(h):
    """Versi teks polos dari HTML hasil render (cadangan kalau rich message gagal)."""
    s = re.sub(r"<br\s*/?>|</p>|</h[1-6]>|</tr>|</blockquote>|<hr\s*/?>", "\n", h)
    s = re.sub(r"</t[dh]>", " | ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = _html.unescape(s)
    s = re.sub(r"[ \t]*\|[ \t]*\n", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def rows_to_text(rows):
    """Kebalikan parser: rows -> teks tombol [Teks|data|style, emo="ID"] per baris."""
    lines = []
    for row in rows:
        toks = []
        for b in row:
            extra = []
            if b["style"]:
                extra.append(b["style"])
            if b["emo"]:
                extra.append(f'emo="{b["emo"]}"')
            tail = ("|" + ", ".join(extra)) if extra else ""
            toks.append(f'[{b["text"]}|{b["data"]}{tail}]')
        lines.append("".join(toks))
    return "\n".join(lines)


MEDIA_KINDS = {
    "photo": ('<img src="{ref}"/>', "photo"),
    "video": ('<video src="{ref}"></video>', "video"),
    "animation": ('<video src="{ref}"></video>', "video"),
}
REF_FORMATS = ("tg://{scheme}?id={id}", "{id}")
_MEDIA_REF_ID = "m0"


def _rich_file(kind, file_id):
    from pyrogram import raw
    from pyrogram.file_id import FileId

    fid = FileId.decode(file_id)
    key = dict(id=fid.media_id, access_hash=fid.access_hash,
               file_reference=fid.file_reference)
    if kind == "photo":
        return raw.types.InputRichFilePhoto(id=_MEDIA_REF_ID, photo=raw.types.InputPhoto(**key))
    return raw.types.InputRichFileDocument(id=_MEDIA_REF_ID, document=raw.types.InputDocument(**key))


def make_rich(html, kind=None, file_id=None, ref_fmt=REF_FORMATS[0]):
    """InputRichMessage: media (opsional) di atas, lalu isi note — satu pesan."""
    from pyrogram import raw
    from pyrogram.types import InputRichMessage

    class _Rich(InputRichMessage):
        def write(self):
            if not (kind and file_id):
                return super().write()
            tag, scheme = MEDIA_KINDS[kind]
            ref = ref_fmt.format(scheme=scheme, id=_MEDIA_REF_ID)
            return raw.types.InputRichMessageHTML(
                html=tag.format(ref=ref) + self.html,
                rtl=self.is_rtl,
                noautolink=self.skip_entity_detection,
                files=[_rich_file(kind, file_id)],
            )

    return _Rich(html=html)
