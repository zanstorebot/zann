from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (adminlist_cmd, block_cmd, remuname_cmd, setbio_cmd,
                     setname_cmd, setonline_cmd, setpp_cmd, setuname_cmd,
                     unblock_cmd)
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Profile"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Profil</b>
`{0}adminlist` : Lihat daftar grup admin
`{0}mestats` : Lihat statistik akun
`{0}setuname` (teks/balas teks) : Ubah username
`{0}remuname` : Hapus username
`{0}setbio` (teks/balas teks) : Ubah bio
`{0}setname` (teks/balas teks) : Ubah nama
`{0}setpp` (balas media) : Ubah foto profil
`{0}block` (username/balas user) : Blokir user
`{0}unblock` (username/balas user) : Buka blokir user
</blockquote>"""


@CMD.UBOT("setonline")
async def _(client, message):
    return await setonline_cmd(client, message)


@CMD.UBOT("unblock")
async def _(client, message):
    return await unblock_cmd(client, message)


@CMD.UBOT("block")
async def _(client, message):
    return await block_cmd(client, message)


@CMD.UBOT("setname")
@CMD.FAKEDEV("setname")
async def _(client, message):
    return await setname_cmd(client, message)


@CMD.UBOT("setuname")
@CMD.FAKEDEV("setuname")
async def _(client, message):
    return await setuname_cmd(client, message)


@CMD.UBOT("remuname")
@CMD.FAKEDEV("remuname")
async def _(client, message):
    return await remuname_cmd(client, message)


@CMD.UBOT("setbio")
@CMD.FAKEDEV("setbio")
async def _(client, message):
    return await setbio_cmd(client, message)


@CMD.UBOT("adminlist")
async def _(client, message):
    return await adminlist_cmd(client, message)


@CMD.UBOT("setpp")
@CMD.FAKEDEV("setpp")
async def _(client, message):
    return await setpp_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Profil"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}adminlist'), cell('Lihat daftar grup admin')],
                    [cell(f'{prefix}mestats'), cell('Lihat statistik akun')],
                    [cell(f'{prefix}setuname'), cell('Ubah username')],
                    [cell(f'{prefix}remuname'), cell('Hapus username')],
                    [cell(f'{prefix}setbio'), cell('Ubah bio')],
                    [cell(f'{prefix}setname'), cell('Ubah nama')],
                    [cell(f'{prefix}setpp'), cell('Ubah foto profil')],
                    [cell(f'{prefix}block'), cell('Blokir user')],
                    [cell(f'{prefix}unblock'), cell('Buka blokir user')],
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
