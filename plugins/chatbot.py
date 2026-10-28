from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from clients import alice
from command import chatbot_cmd, chatbot_trigger
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Chatbot"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Chatbot</b>
`{0}chatbot on` : Aktifkan chatbot di grup
`{0}chatbot off` : Nonaktifkan chatbot di grup
`{0}chatbot status` : Lihat status chatbot
`{0}chatbot role` (teks) : Atur peran chatbot

Catatan: Chatbot merespons saat user membalas pesanmu.
</blockquote>"""


@CMD.UBOT("chatbot")
@CMD.ONLY_GROUP
async def _(client, message):
    return await chatbot_cmd(client, message)


@CMD.NO_CMD("CHATBOT", alice)
async def _(client, message):
    return await chatbot_trigger(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Chatbot"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}chatbot on'), cell('Aktifkan chatbot di grup')],
                    [cell(f'{prefix}chatbot off'), cell('Nonaktifkan chatbot di grup')],
                    [cell(f'{prefix}chatbot status'), cell('Lihat status chatbot')],
                    [cell(f'{prefix}chatbot role'), cell('Atur peran chatbot')],
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
