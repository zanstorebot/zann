from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (antiucast_cmd, allowucast_cmd, disallowucast_cmd,
                     listallowucast_cmd, ucast_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

__MODULES__ = "Anti Ucast"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Anti-PM (Anti-Ucast)</b>
`{0}antipm on/off/status` : Nyalakan, matikan, atau cek status
`{0}pmall` : Mode ALL, hapus semua pesan pribadi masuk
`{0}pmquery` : Mode QUERY, hapus hanya pesan berisi kata terlarang
`{0}pmblok kata1, kata2` : Tambah kata/frasa terlarang
`{0}pmunblok kata` : Hapus kata dari daftar (`all` untuk kosongkan)
`{0}pmlist` : Lihat daftar kata terlarang
`{0}acc` (balas/id/username) : Tambah ke whitelist, di private chat cukup ketik langsung
`{0}unacc` (balas/id/username/all) : Hapus dari whitelist
`{0}listacc` : Lihat whitelist
</blockquote>"""


@CMD.UBOT("antipm")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("pmall")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("pmquery")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("pmblok")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("pmunblok")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("pmlist")
async def _(client, message):
    return await antiucast_cmd(client, message)


@CMD.UBOT("acc")
async def _(client, message):
    return await allowucast_cmd(client, message)


@CMD.UBOT("unacc")
async def _(client, message):
    return await disallowucast_cmd(client, message)


@CMD.UBOT("listacc")
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
            [emo(5242278610089304739, "🤖"), " Perintah Anti-PM"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f"{prefix}antipm on/off/status"), cell("Nyalakan, matikan, atau cek status")],
                    [cell(f"{prefix}pmall"), cell("Mode ALL: hapus semua pesan pribadi masuk")],
                    [cell(f"{prefix}pmquery"), cell("Mode QUERY: hapus hanya pesan berisi kata terlarang")],
                    [cell(f"{prefix}pmblok kata1, kata2"), cell("Tambah kata/frasa terlarang")],
                    [cell(f"{prefix}pmunblok kata/all"), cell("Hapus kata dari daftar")],
                    [cell(f"{prefix}pmlist"), cell("Lihat daftar kata terlarang")],
                    [cell(f"{prefix}acc"), cell("Tambah whitelist (balas/id/username, atau ketik di private chat)")],
                    [cell(f"{prefix}unacc"), cell("Hapus whitelist (balas/id/username/all)")],
                    [cell(f"{prefix}listacc"), cell("Lihat whitelist")],
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