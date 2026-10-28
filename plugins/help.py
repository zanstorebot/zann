from helpers import CMD
from helpers.help_modes import help_cmd, helpmode_cmd
from helpers.rich_footer import footer_table
from pyrogram.helpers import cell, table
from pyrogram.types import InputRichMessage

__MODULES__ = "Mode"
__HELP__ = """<blockquote><b>Mode Tampilan Help</b>

<b>{0}helpmode</b> - lihat mode aktif dan cara pakai.
<b>{0}helpmode simple</b> - teks bantuan asli tanpa tabel.
<b>{0}helpmode table</b> - tabel bantuan asli tiap plugin.
<b>{0}helpmode modern</b> - tabel bantuan plugin dan bubble button.
<b>{0}help</b> - buka daftar kategori/plugins.
<b>{0}help nama_modul</b> - buka bantuan modul.

Mode diganti lewat command, bukan tombol. Tersimpan per pengguna.
{1}</blockquote>"""


async def __HELP_RICH__(client, chat_id, prefix, text_help, message_id=None, prev_page_num=0):
    rich = InputRichMessage(blocks=[
        table([[cell("MODE TAMPILAN HELP", is_header=True, colspan=2, align="center")],
               [cell("Perintah", is_header=True), cell("Keterangan", is_header=True)],
               [cell(f"{prefix}helpmode"), cell("Lihat mode aktif dan cara pakai")],
               [cell(f"{prefix}helpmode simple"), cell("Teks bantuan asli tanpa tabel")],
               [cell(f"{prefix}helpmode table"), cell("Tabel bantuan asli tiap plugin")],
               [cell(f"{prefix}helpmode modern"), cell("Tabel bantuan plugin dan bubble button")],
               [cell(f"{prefix}help"), cell("Buka kategori/plugins")],
               [cell(f"{prefix}help nama_modul"), cell("Buka bantuan modul")]], bordered=True, striped=True),
        footer_table(),
    ])
    if message_id:
        return await client.edit_rich_message(chat_id, message_id, rich)
    return await client.send_rich_message(chat_id, rich)


@CMD.UBOT("help")
async def _(client, message):
    return await help_cmd(client, message)


@CMD.UBOT("helpmode", sudo=False)
async def _(client, message):
    return await helpmode_cmd(client, message)
