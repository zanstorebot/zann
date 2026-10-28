from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import absen_cmd, mping_cmd, settext_cmd
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Settings"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Pengaturan Teks</b>
`{0}set_text ping` (teks/balas teks) : Atur teks ping
`{0}set_text uptime` (teks/balas teks) : Atur teks uptime
`{0}set_text owner` (teks/balas teks) : Atur teks owner
`{0}set_text ubot` (teks/balas teks) : Atur teks userbot
`{0}set_text sukses` (teks/balas teks) : Atur teks sukses gcast
`{0}set_text proses` (teks/balas teks) : Atur teks proses
`{0}set_text help` (teks/balas teks) : Atur teks help
</blockquote>"""


@CMD.UBOT("set_text")
async def _(client, message):
    return await settext_cmd(client, message)


@CMD.UBOT("ping")
@CMD.DEV_CMD("mping")
@CMD.FAKEDEV("mping")
async def _(client, message):
    return await mping_cmd(client, message)


@CMD.FAKEDEV("absen")
@CMD.DEV_CMD("absen")
async def _(client, message):
    return await absen_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Pengaturan Teks"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}set_text ping'), cell('Atur teks ping')],
                    [cell(f'{prefix}set_text uptime'), cell('Atur teks uptime')],
                    [cell(f'{prefix}set_text owner'), cell('Atur teks owner')],
                    [cell(f'{prefix}set_text ubot'), cell('Atur teks userbot')],
                    [cell(f'{prefix}set_text sukses'), cell('Atur teks sukses gcast')],
                    [cell(f'{prefix}set_text proses'), cell('Atur teks proses')],
                    [cell(f'{prefix}set_text help'), cell('Atur teks help')],
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
