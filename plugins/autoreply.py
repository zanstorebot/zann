from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from clients import alice
from command import autoreply_cmd, mentioned_trigger
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Autoreply"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Auto Reply</b>
`{0}autoreply on` : Aktifkan auto reply di grup
`{0}autoreply off` : Nonaktifkan auto reply di grup
`{0}autoreply status` : Lihat status auto reply
</blockquote>"""


@CMD.UBOT("autoreply")
@CMD.ONLY_GROUP
async def _(client, message):
    return await autoreply_cmd(client, message)


@CMD.NO_CMD("MENTIONED", alice)
async def _(client, message):
    return await mentioned_trigger(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Auto Reply"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}autoreply on'), cell('Aktifkan auto reply di grup')],
                    [cell(f'{prefix}autoreply off'), cell('Nonaktifkan auto reply di grup')],
                    [cell(f'{prefix}autoreply status'), cell('Lihat status auto reply')],
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
