from helpers import CMD
from command import (space_efk, petir_efk, fucek_efk, nangis_efk, study_efk, peri_efk,
dingin_efk, pening_efk, like_efk, gud_efk, kesel_efk, unc_efk, huek_efk, wkwk_efk, hantu_efk,
crot_efk, kabom_efk, surga_efk, hp_efk, hujan_efk, nangis2_efk, gojila_efk, love_efk, aaa_efk,
err_efk, pikachu_efk, hmm_efk, error_efk)

from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.types import InputRichMessage, RichTextMarked, RichTextTextMention, RichTextBold, RichTextCustomEmoji
from clients import alice
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

def _make_rich(*blocks):
    builder = RichMessageBuilder()
    for block in blocks:
        builder.add(block)
    return builder.build()


_EFK_CMDS = [
    "space", "petir", "fucek", "😭", "😭😭", "belajar",
    "mimiperi", "dingin", "pening", "like", "gud", "kesal",
    "unicorn", "huek", "wkwk", "hantu", "kabom", "crot",
    "surga", "hp", "hujan", "aaa", "hmmm", "love",
    "rawr", "error", "hah",
]

def _efk_rows(prefix, cols=3):
    cmds = _EFK_CMDS + [""] * (-len(_EFK_CMDS) % cols)  # padding baris terakhir
    rows = [[cell("Perintah", is_header=True) for _ in range(cols)]]
    for i in range(0, len(cmds), cols):
        rows.append([cell(f"{prefix}{c}" if c else "") for c in cmds[i:i + cols]])
    return rows

__MODULES__ = "Efek Pesan"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Efek Animasi Keren</b>
`{0}space`, `{0}petir`, `{0}fucek`, `{0}😭`, `{0}😭😭`, `{0}belajar`
`{0}mimiperi`, `{0}dingin`, `{0}pening`, `{0}like`, `{0}gud`
`{0}kesal`, `{0}unicorn`, `{0}huek`, `{0}wkwk`, `{0}hantu`
`{0}kabom`, `{0}crot`, `{0}surga`, `{0}hp`, `{0}hujan`
`{0}aaa`, `{0}hmmm`, `{0}love`, `{0}rawr`, `{0}error`, `{0}hah`
`{0}tembak`, `{0}bundir`, `{0}y`, `{0}tq`
</blockquote>"""

async def __HELP_RICH__(client, chat_id, prefix, text_help,
                        message_id=None, prev_page_num=0):
    rich = _make_rich(
        divider(),
        table(
            [[cell([emo(5262970276462745484, "💎"), RichTextBold(f" CMD/PREFIXES: {prefix}")], align="center", is_header=True)]],
        ),
        table(
            [[cell([emo(6255910249362885846, "💎"), RichTextBold(f" USER PREMIUM ONLY!")], align="center", is_header=True)]],
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Perintah Efek Pesan"],
            table(
                _efk_rows(prefix),
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


@CMD.UBOT("😭😭")
async def _(client, message):
    return await nangis2_efk(client, message)

@CMD.UBOT("aaa")
async def _(client, message):
    return await aaa_efk(client, message)

@CMD.UBOT("error")
async def _(client, message):
    return await error_efk(client, message)

@CMD.UBOT("eror")
async def _(client, message):
    return await err_efk(client, message)

@CMD.UBOT("hmmm")
async def _(client, message):
    return await hmm_efk(client, message)

@CMD.UBOT("hah")
async def _(client, message):
    return await pikachu_efk(client, message)

@CMD.UBOT("love")
async def _(client, message):
    return await love_efk(client, message)

@CMD.UBOT("rawr")
async def _(client, message):
    return await gojila_efk(client, message)

@CMD.UBOT("hujan")
async def _(client, message):
    return await hujan_efk(client, message)

@CMD.UBOT("hp")
async def _(client, message):
    return await hp_efk(client, message)

@CMD.UBOT("surga")
async def _(client, message):
    return await surga_efk(client, message)

@CMD.UBOT("space")
async def _(client, message):
    return await space_efk(client, message)

@CMD.UBOT("petir")
async def _(client, message):
    return await petir_efk(client, message)

@CMD.UBOT("fucek")
async def _(client, message):
    return await fucek_efk(client, message)

@CMD.UBOT("😭")
async def _(client, message):
    return await nangis_efk(client, message)

@CMD.UBOT("belajar")
async def _(client, message):
    return await study_efk(client, message)

@CMD.UBOT("mimiperi")
async def _(client, message):
    return await peri_efk(client, message)

@CMD.UBOT("dingin")
async def _(client, message):
    return await dingin_efk(client, message)

@CMD.UBOT("pening")
async def _(client, message):
    return await pening_efk(client, message)

@CMD.UBOT("like")
async def _(client, message):
    return await like_efk(client, message)

@CMD.UBOT("gud")
async def _(client, message):
    return await gud_efk(client, message)

@CMD.UBOT("kesal")
async def _(client, message):
    return await kesel_efk(client, message)

@CMD.UBOT("unicorn")
async def _(client, message):
    return await unc_efk(client, message)

@CMD.UBOT("huek")
async def _(client, message):
    return await huek_efk(client, message)

@CMD.UBOT("wkwk")
async def _(client, message):
    return await wkwk_efk(client, message)

@CMD.UBOT("hantu")
async def _(client, message):
    return await hantu_efk(client, message)

@CMD.UBOT("kabom")
async def _(client, message):
    return await kabom_efk(client, message)

@CMD.UBOT("crot")
async def _(client, message):
    return await crot_efk(client, message)
