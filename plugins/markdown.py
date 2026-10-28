from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

__MODULES__ = "Format"
__HELP__ = "<blockquote>**To view markdown format please click on the button below.**</blockquote>"


async def __HELP_RICH__(client, chat_id, prefix, text_help2):
    return await send_rich(
        client,
        chat_id,
        divider(),
          table(
             [
                 [cell([emo(5262970276462745484, "💎"), RichTextBold(f" CMD/PREFIXES: {prefix}")], align="center", is_header=True)],
             ],
          ),
        details(
            [emo(5242278610089304739, "🤖"), " Perintah Markdown"],
            paragraph("Klik tombol di bawah untuk melihat format markdown."),
        ),
        table(
                  [
                    [cell("AliceDevs Core v3.14 ⚡", align="center", is_header=True)],
                  ],
            ),
    )

