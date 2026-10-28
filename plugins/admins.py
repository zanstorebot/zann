from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (ban_cmd, del_cmd, group_cmd, kick_cmd, mute_cmd, pin_cmd,
                     promote_cmd, purge_cmd, purgeme_cmd, report_cmd,
                     staff_cmd, zombies_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Admins"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Admin Grup</b>
`{0}staff` : Lihat daftar admin grup
`{0}purgeme` : Hapus pesan kamu
`{0}purge` : Hapus beberapa pesan
`{0}kick` : Tendang member
`{0}delkick` : Tendang member dan hapus pesan terkait
`{0}ban` : Blokir member
`{0}delban` : Blokir member dan hapus pesan terkait
`{0}unban` : Buka blokir member
`{0}del` : Hapus pesan yang dibalas
`{0}pin` : Sematkan pesan
`{0}unpin` : Lepas sematan pesan
`{0}mute` : Bisukan member
`{0}delmute` : Bisukan member dan hapus pesan terkait
`{0}unmute` : Buka bisu member
`{0}zombies` : Keluarkan akun terhapus
`{0}report` : Laporkan member ke admin
`{0}promote` : Jadikan admin
`{0}fullpromote` : Jadikan admin dengan akses penuh
`{0}demote` : Turunkan admin
`{0}title` (judul) : Ubah judul grup
`{0}group` (judul) : Ubah judul grup
</blockquote>"""


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
            [emo(5242278610089304739, "🤖"), " Perintah Admin Grup"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f"{prefix}kick"), cell("Tendang member grup")],
                    [cell(f"{prefix}ban"), cell("Blokir member grup")],
                    [cell(f"{prefix}unban"), cell("Buka blokir member")],
                    [cell(f"{prefix}mute"), cell("Bisu member grup")],
                    [cell(f"{prefix}unmute"), cell("Buka bisu member grup")],
                    [cell(f"{prefix}zombies"), cell("Tendang akun terhapus dalam grup")],
                    [cell(f"{prefix}pin"), cell("Sematkan pesan")],
                    [cell(f"{prefix}unpin"), cell("Lepas sematan pesan")],
                    [cell(f"{prefix}promote"), cell("Promosi member ke admin grup")],
                    [cell(f"{prefix}staff"), cell("Cek staff admin grup")],
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

@CMD.UBOT("staff")
@CMD.ONLY_GROUP
async def _(client, message):
    return await staff_cmd(client, message)


@CMD.UBOT("purgeme")
async def _(client, message):
    return await purgeme_cmd(client, message)


@CMD.UBOT("purge")
async def _(client, message):
    return await purge_cmd(client, message)


@CMD.UBOT("kick|delkick")
@CMD.ONLY_GROUP
@CMD.ADMIN
async def _(client, message):
    return await kick_cmd(client, message)


@CMD.UBOT("ban|delban|unban")
@CMD.ONLY_GROUP
@CMD.ADMIN
async def _(client, message):
    return await ban_cmd(client, message)


@CMD.UBOT("del")
async def _(client, message):
    return await del_cmd(client, message)


@CMD.UBOT("pin|unpin")
async def _(client, message):
    return await pin_cmd(client, message)


@CMD.UBOT("mute|delmute|unmute")
@CMD.ONLY_GROUP
@CMD.ADMIN
async def _(client, message):
    return await mute_cmd(client, message)


@CMD.UBOT("zombies")
@CMD.ONLY_GROUP
@CMD.ADMIN
async def _(client, message):
    return await zombies_cmd(client, message)


@CMD.UBOT("report")
@CMD.ONLY_GROUP
async def _(client, message):
    return await report_cmd(client, message)


@CMD.UBOT("fullpromote|promote|demote")
@CMD.ONLY_GROUP
@CMD.ADMIN
async def _(client, message):
    return await promote_cmd(client, message)


@CMD.UBOT("title|group")
@CMD.ONLY_GROUP
@CMD.ADMIN
async def _(client, message):
    return await group_cmd(client, message)
