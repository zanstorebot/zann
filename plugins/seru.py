from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import fakex_cmd
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "X Post"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Fake Post X</b>
`{0}fakex` [opsi] (teks) : Bikin gambar postingan X dari teks
    reply orang = pakai nama, username & foto profilnya
    reply/kirim foto = foto ikut jadi media postingan
<b>Opsi</b> (taruh di depan teks):
`dark` / `dim` / `light` : tema
<b>Contoh:</b> `{0}fakex dark Alice Keren 🔥`
</blockquote>"""


@CMD.UBOT("fakex|fakepost")
async def _(client, message):
    return await fakex_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Fake Post X"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}fakex [opsi] (teks)'), cell('Gambar postingan X dari teks')],
                    [cell('reply orang'), cell('Pakai nama & foto profilnya')],
                    [cell('reply / kirim foto'), cell('Foto jadi media postingan')],
                    [cell('dark / dim / light'), cell('Tema')],
                    [cell(f'{prefix}fakex dark Alice Keren 🔥'), cell('Contoh')],
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
