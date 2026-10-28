from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from clients import alice
from command import AUTO_APPROVE, PMPERMIT, nopm_cmd, okpm_cmd, pmpermit_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "PMPermit"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah PM Permit</b>
`{0}pmpermit set on` : Aktifkan PM Permit
`{0}pmpermit set off` : Matikan PM Permit
`{0}pmpermit media` (balas media) : Atur media PM Permit
`{0}pmpermit teks` (teks/balas teks) : Atur pesan PM Permit
`{0}pmpermit warn` (angka) : Atur batas peringatan
`{0}pmpermit get` (status/teks/warn/approved/media) : Lihat pengaturan
`{0}ok` : Setujui user
`{0}no` : Tolak user
`{0}pmpermit disapproved` (username) : Hapus user approved
`{0}pmpermit disapproved all` : Hapus semua user approved
</blockquote>"""


@CMD.UBOT("pmpermit")
async def _(client, message):
    return await pmpermit_cmd(client, message)


@CMD.UBOT("ok")
@CMD.ONLY_PRIVATE
async def _(client, message):
    return await okpm_cmd(client, message)


@CMD.UBOT("no")
@CMD.ONLY_PRIVATE
async def _(client, message):
    return await nopm_cmd(client, message)


@CMD.NO_CMD("PMPERMIT", alice)
@CMD.capture_err
async def _(client, message):
    return await PMPERMIT(client, message)


@CMD.NO_CMD("AUTO_APPROVE", alice)
@CMD.capture_err
async def _(client, message):
    return await AUTO_APPROVE(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah PM Permit"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}pmpermit set on'), cell('Aktifkan PM Permit')],
                    [cell(f'{prefix}pmpermit set off'), cell('Matikan PM Permit')],
                    [cell(f'{prefix}pmpermit media'), cell('Atur media PM Permit')],
                    [cell(f'{prefix}pmpermit teks'), cell('Atur pesan PM Permit')],
                    [cell(f'{prefix}pmpermit warn'), cell('Atur batas peringatan')],
                    [cell(f'{prefix}pmpermit get'), cell('Lihat pengaturan')],
                    [cell(f'{prefix}ok'), cell('Setujui user')],
                    [cell(f'{prefix}no'), cell('Tolak user')],
                    [cell(f'{prefix}pmpermit disapproved'), cell('Hapus user approved')],
                    [cell(f'{prefix}pmpermit disapproved all'), cell('Hapus semua user approved')],
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
