from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pathlib import Path

from command import alfabet_cmd, toxic_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Toxic"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Toxic</b>
Gunakan fitur ini dengan bijak.

<b>Perintah Utama</b>
`{0}ngentot`, `{0}hina`, `{0}ngatain`, `{0}ngaca`
`{0}goblok`, `{0}alay`, `{0}yatim`, `{0}kontol`

<b>Perintah Huruf</b>
`{0}a`, `{0}b`, `{0}c`, `{0}d`, `{0}e`, `{0}f`, `{0}g`, `{0}h`, `{0}i`
`{0}j`, `{0}k`, `{0}l`, `{0}m`, `{0}n`, `{0}o`, `{0}p`, `{0}r`, `{0}s`
`{0}t`, `{0}u`, `{0}v`, `{0}w`, `{0}x`, `{0}z`
</blockquote>"""


@CMD.UBOT("ngentot|ngatain|goblok|yatim|hina|alay|ngaca|kontol")
async def _(client, message):
    return await toxic_cmd(client, message)


@CMD.UBOT("a|b|c|d|e|f|g|h|i|j|k|l|m|o|p|r|s|t|u|v|w|x|z")
async def _(client, message):
    plugin_name = Path(__file__).stem
    print(plugin_name)
    return await alfabet_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Toxic"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}ngentot | {prefix}hina | {prefix}ngatain | {prefix}ngaca'), cell('-')],
                    [cell(f'{prefix}goblok | {prefix}alay | {prefix}yatim | {prefix}kontol'), cell('-')],
                    [cell(f'{prefix}a | {prefix}b | {prefix}c | {prefix}d | {prefix}e | {prefix}f | {prefix}g | {prefix}h | {prefix}i'), cell('-')],
                    [cell(f'{prefix}j | {prefix}k | {prefix}l | {prefix}m | {prefix}n | {prefix}o | {prefix}p | {prefix}r | {prefix}s'), cell('-')],
                    [cell(f'{prefix}t | {prefix}u | {prefix}v | {prefix}w | {prefix}x | {prefix}z'), cell('-')],
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
