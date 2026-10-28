from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (addbcdb_cmd, addbl_cmd, allowucast_cmd, antiucast_cmd,
                     bc_cmd, bcerror_cmd, cancel_cmd, delbcdb_cmd, delbl_cmd,
                     disallowucast_cmd, gcast_cmd, listallowucast_cmd,
                     listbcdb_cmd, listbl_cmd, sendinline_cmd, ucast_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Broadcast"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Broadcast</b>
`{0}bc db` (teks/balas pesan) : Broadcast ke chat database
`{0}bc group` (teks/balas pesan) : Broadcast ke semua grup
`{0}bc private` (teks/balas pesan) : Broadcast ke chat pribadi
`{0}bc all` (teks/balas pesan) : Broadcast ke grup dan chat pribadi
`{0}addbl` (chatid) : Tambahkan chat ke blacklist broadcast
`{0}delbl` (chatid) : Hapus chat dari blacklist broadcast
`{0}listbl` : Lihat blacklist broadcast
`{0}add-bcdb` (chatid) : Tambahkan chat ke database broadcast
`{0}del-bcdb` (chatid) : Hapus chat dari database broadcast
`{0}list-bcdb` : Lihat database broadcast
`{0}cancel` (taskid) : Batalkan broadcast

<b>Perintah Anti-Ucast</b>
`{0}antiucast on/off/status` : Hapus otomatis semua pesan pribadi masuk
`{0}allowucast` (balas/id/username) : Tambahkan ke whitelist anti-ucast
`{0}disallowucast` (balas/id/username/all) : Hapus dari whitelist anti-ucast
`{0}listallowucast` : Lihat whitelist anti-ucast
</blockquote>"""


@CMD.UBOT("bc")
@CMD.FAKEDEV("bc")
async def _(client, message):
    return await bc_cmd(client, message)


@CMD.UBOT("gcast")
@CMD.FAKEDEV("gcast")
@CMD.DEV_CMD("gcast")
async def _(client, message):
    return await gcast_cmd(client, message)


@CMD.UBOT("ucast")
@CMD.FAKEDEV("ucast")
async def _(client, message):
    return await ucast_cmd(client, message)


@CMD.UBOT("bc-error")
@CMD.FAKEDEV("bc-error")
async def _(client, message):
    return await bcerror_cmd(client, message)


@CMD.UBOT("cancel")
@CMD.FAKEDEV("cancel")
async def _(client, message):
    return await cancel_cmd(client, message)


@CMD.UBOT("addbl")
@CMD.DEV_CMD("addbl")
@CMD.FAKEDEV("addbl")
async def _(client, message):
    return await addbl_cmd(client, message)


@CMD.UBOT("delbl")
@CMD.DEV_CMD("delbl")
@CMD.FAKEDEV("delbl")
async def _(client, message):
    return await delbl_cmd(client, message)


@CMD.UBOT("listbl")
@CMD.FAKEDEV("listbl")
async def _(client, message):
    return await listbl_cmd(client, message)


@CMD.UBOT("add-bcdb")
async def _(client, message):
    return await addbcdb_cmd(client, message)


@CMD.UBOT("del-bcdb")
async def _(client, message):
    return await delbcdb_cmd(client, message)


@CMD.UBOT("list-bcdb")
async def _(client, message):
    return await listbcdb_cmd(client, message)


@CMD.UBOT("send")
async def _(client, message):
    return await sendinline_cmd(client, message)


@CMD.UBOT("antiucast")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("allowucast")
async def _(client, message):
    return await allowucast_cmd(client, message)


@CMD.UBOT("disallowucast")
async def _(client, message):
    return await disallowucast_cmd(client, message)


@CMD.UBOT("listallowucast")
async def _(client, message):
    return await listallowucast_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Broadcast"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}bc db'), cell('Broadcast ke chat database')],
                    [cell(f'{prefix}bc group'), cell('Broadcast ke semua grup')],
                    [cell(f'{prefix}bc private'), cell('Broadcast ke chat pribadi')],
                    [cell(f'{prefix}bc all'), cell('Broadcast ke grup dan chat pribadi')],
                    [cell(f'{prefix}addbl'), cell('Tambahkan chat ke blacklist broadcast')],
                    [cell(f'{prefix}delbl'), cell('Hapus chat dari blacklist broadcast')],
                    [cell(f'{prefix}listbl'), cell('Lihat blacklist broadcast')],
                    [cell(f'{prefix}add-bcdb'), cell('Tambahkan chat ke database broadcast')],
                    [cell(f'{prefix}del-bcdb'), cell('Hapus chat dari database broadcast')],
                    [cell(f'{prefix}list-bcdb'), cell('Lihat database broadcast')],
                    [cell(f'{prefix}cancel'), cell('Batalkan broadcast')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Perintah Anti-Ucast"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}antiucast on/off/status'), cell('Hapus otomatis semua pesan pribadi masuk')],
                    [cell(f'{prefix}allowucast'), cell('Tambahkan ke whitelist (balas/id/username)')],
                    [cell(f'{prefix}disallowucast'), cell('Hapus dari whitelist (balas/id/username/all)')],
                    [cell(f'{prefix}listallowucast'), cell('Lihat whitelist anti-ucast')],
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
