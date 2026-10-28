from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.types import InputRichMessage, RichTextMarked, RichTextTextMention, RichTextBold, RichTextCustomEmoji
from clients import alice
from helpers import AFK_, CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

@CMD.UBOT("listefek")
async def _(client, message):
    return await AFK_.list_efek(client, message)

@CMD.UBOT("afk")
async def _(client, message):
    return await AFK_.set_afk(client, message)


@CMD.NO_CMD("AFK", alice)
@CMD.capture_err
async def _(client, message):
    return await AFK_.get_afk(client, message)


@CMD.UBOT("unafk")
async def _(client, message):
    return await AFK_.unset_afk(client, message)


def _make_rich(*blocks):
    builder = RichMessageBuilder()
    for block in blocks:
        builder.add(block)
    return builder.build()

__MODULES__ = "Afk"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Afk</b>
`{0}afk` : Aktifkan pesan saat sedang offline
`{0}unafk` : Nonaktifkan pesan AFK
`{0}listefek` : List efek pesan AFK
</blockquote>"""


async def __HELP_RICH__(client, chat_id, prefix, text_help,
                        message_id=None, prev_page_num=0):
    rich = _make_rich(
        divider(),
        table(
            [[cell([emo(5262970276462745484, "💎"), RichTextBold(f" CMD/PREFIXES: {prefix}")], align="center", is_header=True)]],
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Perintah AFK"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}afk'), cell('Aktifkan pesan saat sedang offline')],
                    [cell(f'{prefix}unfk'), cell('Nonaktifkan pesan AFK')],
                    [cell(f'{prefix}listefek'), cell('List efek pesan AFK')],
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
