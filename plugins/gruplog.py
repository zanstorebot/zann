from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from clients import alice
from command import (ADD_ME, DELETED, EDITED, KICK_ME, LOGS_GROUP, REPLY,
                     logs_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Logs"

__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Group Log</b>
`{0}logs` (on/off) : Aktifkan atau nonaktifkan group log
</blockquote>"""


@CMD.UBOT("logs")
async def _(client, message):
    return await logs_cmd(client, message)


@CMD.NO_CMD("LOGS_GROUP", alice)
async def _(client, message):
    return await LOGS_GROUP(client, message)


@CMD.NO_CMD("REPLY", alice)
@CMD.IS_LOG
async def _(client, message):
    return await REPLY(client, message)


@CMD.EDITED()
async def _(client, message):
    return await EDITED(client, message)


@CMD.NO_CMD("ADD_ME", alice)
async def _(client, message):
    return await ADD_ME(client, message)


@CMD.NO_CMD("KICK_ME", alice)
async def _(client, message):
    return await KICK_ME(client, message)


@CMD.DELETED()
async def _(client, messages):
    return await DELETED(client, messages)


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
            [emo(5242278610089304739, "🤖"), " Perintah Group Log"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}logs'), cell('Aktifkan atau nonaktifkan group log')],
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
