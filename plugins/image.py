from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (blur_cmd, gif_cmd, miror_cmd, negative_cmd, pic_cmd,
                     rbg_cmd, waifu_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Image"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Gambar</b>
`{0}rbg` (balas gambar) : Hapus background gambar
`{0}blur` (balas gambar) : Beri efek blur
`{0}mirror` (balas gambar) : Balik gambar
`{0}negative` (balas gambar) : Beri efek negatif
`{0}wall` : Cari wallpaper
`{0}waifu` : Cari gambar anime
`{0}pic` (kata kunci) : Cari gambar
`{0}gif` (kata kunci) : Cari GIF
</blockquote>"""


@CMD.UBOT("rbg")
async def _(client, message):
    return await rbg_cmd(client, message)


@CMD.UBOT("blur")
async def _(client, message):
    return await blur_cmd(client, message)


@CMD.UBOT("negative")
async def _(client, message):
    return await negative_cmd(client, message)


@CMD.UBOT("miror")
async def _(client, message):
    return await miror_cmd(client, message)


@CMD.UBOT("wall|waifu")
async def _(client, message):
    return await waifu_cmd(client, message)


@CMD.UBOT("pic")
async def _(client, message):
    return await pic_cmd(client, message)


@CMD.UBOT("gif")
async def _(client, message):
    return await gif_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Gambar"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}rbg'), cell('Hapus background gambar')],
                    [cell(f'{prefix}blur'), cell('Beri efek blur')],
                    [cell(f'{prefix}mirror'), cell('Balik gambar')],
                    [cell(f'{prefix}negative'), cell('Beri efek negatif')],
                    [cell(f'{prefix}wall'), cell('Cari wallpaper')],
                    [cell(f'{prefix}waifu'), cell('Cari gambar anime')],
                    [cell(f'{prefix}pic'), cell('Cari gambar')],
                    [cell(f'{prefix}gif'), cell('Cari GIF')],
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
