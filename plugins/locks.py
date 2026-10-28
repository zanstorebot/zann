from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import l_t, locks_cmd, lockunlock_cmd
from helpers import CMD, Emoji
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Locks"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Kunci Chat</b>
`{0}locktypes` : Lihat jenis izin yang dapat dikunci
`{0}locks` : Lihat izin chat
`{0}lock` (jenis) : Kunci izin chat
`{0}unlock` (jenis) : Buka kunci izin chat
</blockquote>"""


@CMD.UBOT("locktypes")
async def _(client, message):
    em = Emoji(client)
    await em.get()
    await message.reply_text(l_t)
    return


@CMD.UBOT("lock|unlock")
async def _(client, message):
    return await lockunlock_cmd(client, message)


@CMD.UBOT("locks")
async def _(client, message):
    return await locks_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Kunci Chat"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}locktypes'), cell('Lihat jenis izin yang dapat dikunci')],
                    [cell(f'{prefix}locks'), cell('Lihat izin chat')],
                    [cell(f'{prefix}lock'), cell('Kunci izin chat')],
                    [cell(f'{prefix}unlock'), cell('Buka kunci izin chat')],
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
