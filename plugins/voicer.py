from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import stt_cmd, tts_cmd, vremover_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Voice"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Voice</b>
`{0}tts` (teks/balas teks) : Ubah teks menjadi suara
`{0}stt` (balas audio) : Ubah suara menjadi teks
`{0}vremover` (balas audio) : Pisahkan atau hilangkan vokal/instrumen dari audio
</blockquote>"""


@CMD.UBOT("vremover")
async def _(client, message):
    return await vremover_cmd(client, message)


@CMD.UBOT("tts")
async def _(client, message):
    return await tts_cmd(client, message)


@CMD.UBOT("stt")
async def _(client, message):
    return await stt_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Voice"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}tts'), cell('Ubah teks menjadi suara')],
                    [cell(f'{prefix}stt'), cell('Ubah suara menjadi teks')],
                    [cell(f'{prefix}vremover'), cell('Pisahkan atau hilangkan vokal/instrumen dari audio')],
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
