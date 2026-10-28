"""
Helper untuk membangun struktur raw.types.RichText / PageBlock secara manual,
sesuai constructor Pyrogram raw yang sudah diverifikasi dari source (layer 227):

  TextPlain(text: str)
  TextBold(text: RichText)
  TextItalic(text: RichText)
  TextUrl(text: RichText, url: str, webpage_id: int)   # webpage_id WAJIB, isi 0 jika tidak ada
  TextConcat(texts: List[RichText])
  TextEmpty()
  PageCaption(text: RichText, credit: RichText)
  PageBlockParagraph(text: RichText)
  PageBlockPhoto(photo_id: int, caption: PageCaption, spoiler=None, url=None, webpage_id=None)
  PageBlockTable(title: RichText, rows: List[PageTableRow], bordered=None, striped=None)

Semua field yang tipenya RichText/PageBlock/PageCaption dsb HARUS berupa
instance raw.types.* (punya method .write()), BUKAN string biasa dan BUKAN
raw.types.RichText* level tinggi dari pyrogram.types (yang itu untuk API
Bot/Client, beda namespace dengan pyrogram.raw.types).
"""

from pyrogram.raw.types import (
    TextPlain,
    TextBold,
    TextItalic,
    TextUrl,
    TextConcat,
    TextEmpty,
    PageCaption,
    PageBlockParagraph,
    PageBlockPhoto,
)


def plain(text: str):
    """Bungkus string biasa jadi RichText.TextPlain."""
    if not text:
        return TextEmpty()
    return TextPlain(text=text)


def bold(text: str):
    return TextBold(text=plain(text))


def italic(text: str):
    return TextItalic(text=plain(text))


def link(text: str, url: str, webpage_id: int = 0):
    """webpage_id wajib diisi oleh constructor TextUrl -> default 0 jika tak ada webpage."""
    return TextUrl(text=plain(text), url=url, webpage_id=webpage_id)


def concat(*parts):
    """
    Gabungkan beberapa RichText jadi satu (mis. campur plain + bold + url
    dalam satu paragraf). Terima string biasa juga -> otomatis dibungkus plain().
    """
    texts = [p if hasattr(p, "write") else plain(p) for p in parts]
    return TextConcat(texts=texts)


def build_caption(text_richtext, credit_richtext=None):
    """
    PageCaption butuh dua RichText: text dan credit.
    credit boleh kosong -> pakai TextEmpty().
    """
    return PageCaption(
        text=text_richtext if hasattr(text_richtext, "write") else plain(text_richtext),
        credit=credit_richtext if credit_richtext is not None else TextEmpty(),
    )


def build_paragraph_block(text_richtext):
    """Bangun PageBlockParagraph dari RichText (atau string biasa)."""
    rt = text_richtext if hasattr(text_richtext, "write") else plain(text_richtext)
    return PageBlockParagraph(text=rt)


def build_photo_block(photo_id: int, caption_text: str = "", caption_credit: str = None,
                       spoiler: bool = None, url: str = None, webpage_id: int = None):
    """
    Bangun PageBlockPhoto lengkap dengan PageCaption di dalamnya.

    photo_id  : ID foto asli (long) - sama dengan InputPhoto.id, BUKAN index list.
    spoiler   : True/False/None - flags.1
    url       : opsional, flags.0 (biasanya untuk foto dari webpage preview)
    webpage_id: opsional, flags.0 (pasangan dari url)
    """
    caption = build_caption(caption_text, caption_credit)
    return PageBlockPhoto(
        photo_id=photo_id,
        caption=caption,
        spoiler=spoiler,
        url=url,
        webpage_id=webpage_id,
    )


if __name__ == "__main__":
    # Contoh pemakaian
    para = build_paragraph_block(
        concat("Ini teks ", bold("tebal"), " dan ", italic("miring"), " serta ",
               link("tautan", "https://example.com"))
    )
    photo_block = build_photo_block(
        photo_id=1234567890123,
        caption_text="Contoh caption foto",
    )

    # Serialize untuk memastikan tidak ada exception (harus menghasilkan bytes)
    print("paragraph bytes len:", len(para.write()))
    print("photo block bytes len:", len(photo_block.write()))