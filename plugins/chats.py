from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (cc_cmd, cekmember_cmd, cekmsg_cmd, cekonline_cmd,
                     create_cmd, endchat_cmd, getlink_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Chats"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Chat</b>
`{0}cc` (username/balas user) : Hapus pesan user di grup
`{0}endchat bot` : Hapus riwayat chat bot
`{0}endchat private` : Hapus riwayat chat pribadi
`{0}endchat all` : Hapus riwayat bot dan chat pribadi
`{0}endchat` (username/balas user) : Hapus riwayat chat user
`{0}create ch` : Buat channel
`{0}create gc` : Buat supergrup
`{0}getlink` : Buat link undangan chat
`{0}cekmember` : Lihat total member chat
`{0}cekonline` : Lihat member online
`{0}cekmsg` (username/balas user) : Lihat jumlah pesan user
</blockquote>"""


@CMD.UBOT("cc")
async def _(client, message):
    return await cc_cmd(client, message)


@CMD.UBOT("endchat")
async def _(client, message):
    return await endchat_cmd(client, message)


@CMD.UBOT("create")
async def _(client, message):
    return await create_cmd(client, message)


@CMD.UBOT("getlink")
@CMD.ADMIN
async def _(client, message):
    return await getlink_cmd(client, message)


@CMD.UBOT("cekmember")
async def _(client, message):
    return await cekmember_cmd(client, message)


@CMD.UBOT("cekonline")
async def _(client, message):
    return await cekonline_cmd(client, message)


@CMD.UBOT("cekmsg")
async def _(client, message):
    return await cekmsg_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Chat"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}cc'), cell('Hapus pesan user di grup')],
                    [cell(f'{prefix}endchat bot'), cell('Hapus riwayat chat bot')],
                    [cell(f'{prefix}endchat private'), cell('Hapus riwayat chat pribadi')],
                    [cell(f'{prefix}endchat all'), cell('Hapus riwayat bot dan chat pribadi')],
                    [cell(f'{prefix}endchat'), cell('Hapus riwayat chat user')],
                    [cell(f'{prefix}create ch'), cell('Buat channel')],
                    [cell(f'{prefix}create gc'), cell('Buat supergrup')],
                    [cell(f'{prefix}getlink'), cell('Buat link undangan chat')],
                    [cell(f'{prefix}cekmember'), cell('Lihat total member chat')],
                    [cell(f'{prefix}cekonline'), cell('Lihat member online')],
                    [cell(f'{prefix}cekmsg'), cell('Lihat jumlah pesan user')],
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
