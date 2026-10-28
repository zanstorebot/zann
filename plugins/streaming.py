from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from clients import alice
from command import (channelplay_cmd, end_cmd, group_call_ends, pause_cmd,
                     play_cmd, playlist_cmd, resume_cmd, skip_cmd, volume_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Music"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Music</b>
`{0}play` (judul) : Putar audio di voice chat
`{0}vplay` (judul) : Putar video di voice chat
`{0}resume` : Lanjutkan pemutaran
`{0}pause` : Jeda pemutaran
`{0}skip` : Lewati lagu atau video saat ini
`{0}end` : Akhiri pemutaran

<b>Channel Play</b>
`{0}cplay` (judul) : Putar audio di channel
`{0}cvplay` (judul) : Putar video di channel
`{0}cresume` : Lanjutkan pemutaran channel
`{0}cpause` : Jeda pemutaran channel
`{0}cskip` : Lewati media di channel
`{0}cend` : Akhiri pemutaran channel
`{0}channelplay linked` : Hubungkan channel pemutaran dengan chat
`{0}channelplay disable` : Nonaktifkan channel yang terhubung
`{0}channelplay status` : Lihat status channel pemutaran

<b>Lainnya</b>
`{0}volume` (1-200) : Atur volume pemutaran
`{0}playlist` : Lihat playlist yang sedang diputar
</blockquote>"""


@alice.group_call_ends()
async def _(client, update):
    return await group_call_ends(client, update)


@CMD.UBOT("play|vplay|cplay|cvplay")
async def _(client, message):
    return await play_cmd(client, message)


@CMD.UBOT("resume|cresume")
async def _(client, message):
    return await resume_cmd(client, message)


@CMD.UBOT("end|cend")
async def _(client, message):
    return await end_cmd(client, message)


@CMD.UBOT("pause|cpause")
async def _(client, message):
    return await pause_cmd(client, message)


@CMD.UBOT("skip|cskip")
async def _(client, message):
    return await skip_cmd(client, message)


@CMD.UBOT("playlist|cplaylist")
async def _(client, message):
    return await playlist_cmd(client, message)


@CMD.UBOT("volume|cvolume")
async def _(client, message):
    return await volume_cmd(client, message)


@CMD.UBOT("channelplay")
async def _(client, message):
    return await channelplay_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Music"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}play'), cell('Putar audio di voice chat')],
                    [cell(f'{prefix}vplay'), cell('Putar video di voice chat')],
                    [cell(f'{prefix}resume'), cell('Lanjutkan pemutaran')],
                    [cell(f'{prefix}pause'), cell('Jeda pemutaran')],
                    [cell(f'{prefix}skip'), cell('Lewati lagu atau video saat ini')],
                    [cell(f'{prefix}end'), cell('Akhiri pemutaran')],
                    [cell(f'{prefix}cplay'), cell('Putar audio di channel')],
                    [cell(f'{prefix}cvplay'), cell('Putar video di channel')],
                    [cell(f'{prefix}cresume'), cell('Lanjutkan pemutaran channel')],
                    [cell(f'{prefix}cpause'), cell('Jeda pemutaran channel')],
                    [cell(f'{prefix}cskip'), cell('Lewati media di channel')],
                    [cell(f'{prefix}cend'), cell('Akhiri pemutaran channel')],
                    [cell(f'{prefix}channelplay linked'), cell('Hubungkan channel pemutaran dengan chat')],
                    [cell(f'{prefix}channelplay disable'), cell('Nonaktifkan channel yang terhubung')],
                    [cell(f'{prefix}channelplay status'), cell('Lihat status channel pemutaran')],
                    [cell(f'{prefix}volume'), cell('Atur volume pemutaran')],
                    [cell(f'{prefix}playlist'), cell('Lihat playlist yang sedang diputar')],
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
