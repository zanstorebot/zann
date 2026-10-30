from pyrogram.enums import ButtonStyle
from pyrogram.helpers import RichMessageBuilder, cell, details, divider, ikb, table
from pyrogram.types import RichTextBold

from command.maker_command import maker_img_cmd
from helpers import CMD
from helpers.emoprem import emo
from helpers.rich_footer import footer_table

__MODULES__ = "Maker"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Maker</b>
Reply foto atau pesan user:
`{0}maker ektp Contoh Nama laki`
`{0}maker ektp Contoh Nama perempuan`
`{0}maker beautiful`
`{0}maker delete`
`{0}maker facepalm`
`{0}maker xnxx Judul gambar`

Tanpa reply:
`{0}maker sertifikat Contoh Nama`
`{0}maker ephoto360 URL_EFEK | Teks`

Mode: `ektp`, `delete`, `beautiful`, `xnxx`, `facepalm`, `sertifikat`, `ephoto360`
</blockquote>"""


@CMD.UBOT("maker")
async def _(client, message):
    return await maker_img_cmd(client, message)


def _make_rich(*blocks):
    builder = RichMessageBuilder()
    for block in blocks:
        builder.add(block)
    return builder.build()


async def __HELP_RICH__(client, chat_id, prefix, text_help, message_id=None, prev_page_num=0):
    rich = _make_rich(
        divider(),
        table([[cell([emo(5262970276462745484, "💎"), RichTextBold(f" CMD/PREFIXES: {prefix}")], align="center", is_header=True)]]),
        details(
            [emo(5242278610089304739, "🤖"), " Perintah Maker"],
            table([
                [cell("Perintah"), cell("Keterangan")],
                [cell(f"{prefix}maker ektp <nama> <laki/perempuan>"), cell("Buat eKTP dengan data fiktif; reply user atau foto")],
                [cell(f"{prefix}maker beautiful"), cell("Efek beautiful; reply user atau foto")],
                [cell(f"{prefix}maker delete"), cell("Efek delete; reply user atau foto")],
                [cell(f"{prefix}maker facepalm"), cell("Efek facepalm; reply user atau foto")],
                [cell(f"{prefix}maker xnxx <judul>"), cell("Buat canvas judul; reply user atau foto")],
                [cell(f"{prefix}maker sertifikat <teks>"), cell("Buat sertifikat; tanpa reply")],
                [cell(f"{prefix}maker ephoto360 <URL efek> | <teks>"), cell("Buat efek teks Ephoto360; tanpa reply")],
            ], bordered=True, striped=True),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Cara Penggunaan"],
            table([
                [cell("Sumber foto"), cell("Reply foto, atau reply pesan user")],
                [cell("Contoh eKTP"), cell(f"{prefix}maker ektp Bujang laki")],
            ], bordered=True, striped=True),
        ),
        divider(),
        footer_table(),
    )
    button = ikb([[("Back", f"help_back({prev_page_num})", ButtonStyle.DANGER, "5258330865674494479")]])
    if message_id:
        return await client.edit_rich_message(chat_id, message_id, rich, reply_markup=button)
    return await client.send_rich_message(chat_id, rich, reply_markup=button)