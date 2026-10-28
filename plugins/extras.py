from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (bl_leave, cleardb_leave, getbl_leave, getmute_cmd,
                     join_cmd, kickme_cmd, leave_cmd, unbl_leave)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Extras"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Extras</b>
`{0}leave channel` : Keluar dari semua channel
`{0}leave group` : Keluar dari semua grup
`{0}leave global` : Keluar dari semua grup dan channel
`{0}leave mute` : Keluar dari grup yang membatasi akunmu
`{0}join` (chatid/URL/username) : Bergabung ke chat
`{0}kickme` : Keluar dari chat saat ini
`{0}bl-leave` (chatid) : Tambah blacklist leave
`{0}unbl-leave` (chatid) : Hapus blacklist leave
`{0}getbl-leave` : Lihat blacklist leave
`{0}cleardb-leave` : Hapus semua blacklist leave
`{0}getmute` : Lihat grup yang membatasi akunmu
</blockquote>"""


@CMD.UBOT("getmute")
@CMD.FAKEDEV("getmute")
async def _(client, message):
    return await getmute_cmd(client, message)


@CMD.UBOT("join")
@CMD.FAKEDEV("join")
async def _(client, message):
    return await join_cmd(client, message)


@CMD.UBOT("kickme")
async def _(client, message):
    return await kickme_cmd(client, message)


@CMD.UBOT("leave")
@CMD.FAKEDEV("leave")
async def _(client, message):
    return await leave_cmd(client, message)


@CMD.UBOT("bl-leave")
async def _(client, message):
    return await bl_leave(client, message)


@CMD.UBOT("unbl-leave")
async def _(client, message):
    return await unbl_leave(client, message)


@CMD.UBOT("getbl-leave")
async def _(client, message):
    return await getbl_leave(client, message)


@CMD.UBOT("cleardb-leave")
async def _(client, message):
    return await cleardb_leave(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Extras"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}leave channel'), cell('Keluar dari semua channel')],
                    [cell(f'{prefix}leave group'), cell('Keluar dari semua grup')],
                    [cell(f'{prefix}leave global'), cell('Keluar dari semua grup dan channel')],
                    [cell(f'{prefix}leave mute'), cell('Keluar dari grup yang membatasi akunmu')],
                    [cell(f'{prefix}join'), cell('Bergabung ke chat')],
                    [cell(f'{prefix}kickme'), cell('Keluar dari chat saat ini')],
                    [cell(f'{prefix}bl-leave'), cell('Tambah blacklist leave')],
                    [cell(f'{prefix}unbl-leave'), cell('Hapus blacklist leave')],
                    [cell(f'{prefix}getbl-leave'), cell('Lihat blacklist leave')],
                    [cell(f'{prefix}cleardb-leave'), cell('Hapus semua blacklist leave')],
                    [cell(f'{prefix}getmute'), cell('Lihat grup yang membatasi akunmu')],
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
