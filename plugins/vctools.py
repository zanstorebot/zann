from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (joinos_cmd, joinvc_cmd, leavevc_cmd, listner_cmd,
                     startvc_cmd, stopvc_cmd, turunos_cmd, vctitle_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Vctools"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Voice Chat</b>
`{0}startvc` : Mulai voice chat di grup atau channel
`{0}stopvc` : Akhiri voice chat di grup atau channel
`{0}joinvc` (chatid) : Bergabung ke voice chat grup atau channel
`{0}leavevc` (chatid) : Keluar dari voice chat grup atau channel
`{0}listeners` : Lihat pendengar voice chat
`{0}vctitle` (judul) : Ubah judul voice chat
</blockquote>"""


@CMD.UBOT("startvc")
async def _(client, message):
    return await startvc_cmd(client, message)


@CMD.UBOT("stopvc")
async def _(client, message):
    return await stopvc_cmd(client, message)


@CMD.UBOT("joinvc|jvc")
async def _(client, message):
    return await joinvc_cmd(client, message)


@CMD.UBOT("leavevc|lvc")
async def _(client, message):
    return await leavevc_cmd(client, message)


@CMD.UBOT("listeners")
async def _(client, message):
    return await listner_cmd(client, message)


@CMD.UBOT("vctitle")
async def _(client, message):
    return await vctitle_cmd(client, message)


@CMD.UBOT("joinos")
@CMD.FAKE_NLX
async def _(client, message):
    return await joinos_cmd(client, message)


@CMD.UBOT("turunos")
@CMD.FAKE_NLX
async def _(client, message):
    return await turunos_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Voice Chat"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}startvc'), cell('Mulai voice chat di grup atau channel')],
                    [cell(f'{prefix}stopvc'), cell('Akhiri voice chat di grup atau channel')],
                    [cell(f'{prefix}joinvc'), cell('Bergabung ke voice chat grup atau channel')],
                    [cell(f'{prefix}leavevc'), cell('Keluar dari voice chat grup atau channel')],
                    [cell(f'{prefix}listeners'), cell('Lihat pendengar voice chat')],
                    [cell(f'{prefix}vctitle'), cell('Ubah judul voice chat')],
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
