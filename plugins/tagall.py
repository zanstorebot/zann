from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from command import all_cmd
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

__MODULES__ = "Tagall"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Tag</b>
`{0}tagall` (teks/balas teks) : Mention semua member chat
`@admins` (teks/balas teks) : Mention semua admin chat
`{0}cancel` (taskid) : Hentikan tugas mention
</blockquote>"""


@CMD.UBOT("all|tagall")
@CMD.ONLY_GROUP
async def _(client, message):
    return await all_cmd(client, message)


@CMD.UBOT_REGEX(r"^(@admins)")
@CMD.ONLY_GROUP
async def _(client, message):
    return await tagadmins_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Tag"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}tagall'), cell('Mention semua member chat')],
                    [cell('@admins'), cell('Mention semua admin chat')],
                    [cell(f'{prefix}cancel'), cell('Hentikan tugas mention')],
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
