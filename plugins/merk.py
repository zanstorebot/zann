from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import ios_cmd, marina_cmd, nulis_cmd, spanduk_cmd, sutra_cmd
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Merk"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Marina</b>
`{0}marina` (reply user) : Foto profil di tengah bunga lotion Marina
`{0}marina` (teks) (reply user) : Logo "Marina" diganti teks sendiri
<b>Contoh:</b> `{0}marina Alice`

<b>Sutra</b>
`{0}sutra` (reply user) : Foto profil di oval kemasan Sutra
`{0}sutra` (teks) (reply user) 
<b>Contoh:</b> `{0}sutra Kondom Lokal`

<b>Nulis</b>
`{0}nulis` (teks) : Teks ditulis tangan di kertas bergaris
`{0}nulis` (reply pesan) : Teks diambil dari pesan yang di-reply
<b>Contoh:</b> `{0}nulis Halo guys, ini tugas saya`

<b>Spanduk</b>
`{0}spanduk` (teks) : Judul spanduk Pecel Lele diganti teks sendiri
`{0}spanduk` (reply pesan) : Teks diambil dari pesan yang di-reply
<b>Contoh:</b> `{0}spanduk Warung Bu Tini`

<b>WhatsApp iOS</b>
`{0}ios` [light/dark] (teks) : Screenshot pesan WA iOS ditekan lama
`{0}ios` [light/dark] (reply pesan) : Teks diambil dari pesan yang di-reply
<b>Contoh:</b> `{0}ios light I love you 💕`

Marina & Sutra: tanpa reply = foto profil sendiri, hasil foto HD.
</blockquote>"""


@CMD.UBOT("marina")
async def _(client, message):
    return await marina_cmd(client, message)


@CMD.UBOT("sutra")
async def _(client, message):
    return await sutra_cmd(client, message)


@CMD.UBOT("nulis")
async def _(client, message):
    return await nulis_cmd(client, message)


@CMD.UBOT("spanduk")
async def _(client, message):
    return await spanduk_cmd(client, message)


@CMD.UBOT("ios")
async def _(client, message):
    return await ios_cmd(client, message)


def _make_rich(*blocks):
    builder = RichMessageBuilder()
    for block in blocks:
        builder.add(block)
    return builder.build()


async def __HELP_RICH__(client, chat_id, prefix, text_help,
                        message_id=None, prev_page_num=0):
    rich = _make_rich(
        divider(),
        table(
            [[cell([emo(5262970276462745484, "💎"), RichTextBold(f" CMD/PREFIXES: {prefix}")], align="center", is_header=True)]],
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Marina"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}marina (reply)'), cell('Foto profil di tengah bunga')],
                    [cell(f'{prefix}marina (teks) (reply)'), cell('Logo Marina diganti teks')],
                    [cell('tanpa reply'), cell('Pakai foto profil sendiri')],
                    [cell(f'{prefix}marina Alice'), cell('Contoh')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Sutra"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}sutra (reply)'), cell('Foto profil di oval kemasan')],
                    [cell(f'{prefix}sutra (teks) (reply)'), cell('Tulisan KONDOM IMPOR diganti')],
                    [cell('tanpa reply'), cell('Pakai foto profil sendiri')],
                    [cell(f'{prefix}sutra Kondom Lokal'), cell('Contoh')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Nulis"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}nulis (teks)'), cell('Ditulis tangan di kertas bergaris')],
                    [cell(f'{prefix}nulis (reply pesan)'), cell('Teks dari pesan yang di-reply')],
                    [cell(f'{prefix}nulis Halo guys'), cell('Contoh')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Spanduk"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}spanduk (teks)'), cell('Judul spanduk Pecel Lele diganti')],
                    [cell(f'{prefix}spanduk (reply pesan)'), cell('Teks dari pesan yang di-reply')],
                    [cell(f'{prefix}spanduk Warung Bu Tini'), cell('Contoh')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " WhatsApp iOS"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}ios light (teks)'), cell('Tema terang')],
                    [cell(f'{prefix}ios dark (teks)'), cell('Tema gelap (default)')],
                    [cell(f'{prefix}ios (reply pesan)'), cell('Teks dari pesan yang di-reply')],
                    [cell(f'{prefix}ios light I love you 💕'), cell('Contoh')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        divider(),
        footer_table(),
    )
    button = ikb(
        [
            [
                (
                    "Back",
                    f"help_back({prev_page_num})",
                    ButtonStyle.DANGER,
                    "5258330865674494479",
                ),
            ],
        ]
    )
    if message_id:
        return await client.edit_rich_message(
            chat_id, message_id, rich, reply_markup=button
        )
    return await client.send_rich_message(chat_id, rich, reply_markup=button)
