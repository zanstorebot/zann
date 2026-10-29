from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import fakex_cmd
from command.seru_command import clone_cmd, restore_profile_cmd
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "X Post"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Fake Post X</b>
`{0}fakex` [opsi] (teks) : Bikin gambar postingan X dari teks
    reply orang = pakai nama, username & foto profilnya
    reply/kirim foto = foto ikut jadi media postingan
<b>Opsi</b> (taruh di depan teks):
`dark` / `dim` / `light` : tema
<b>Contoh:</b> `{0}fakex dark Alice Keren 🔥`

<b>Clone & Restore Profil</b>
`{0}clone` (reply user) : Salin nama, bio & foto profil user
`{0}restore` : Kembalikan profil awal sebelum clone
    Backup otomatis di database sebelum clone pertama
    Clone berulang tidak menimpa backup sampai restore berhasil
    Restore hanya menghapus foto yang dibuat fitur clone
    Clone versi lama tanpa backup tidak bisa dipulihkan otomatis
    Hanya pemilik akun; username tidak diubah
    Foto target tidak tersedia/tersembunyi dilewati
    Gunakan dengan persetujuan target, bukan untuk menipu
</blockquote>"""


@CMD.UBOT("fakex|fakepost")
async def _(client, message):
    return await fakex_cmd(client, message)


@CMD.UBOT("clone")
async def clone_handler(client, message):
    return await clone_cmd(client, message)


@CMD.UBOT("restore")
async def restore_profile_handler(client, message):
    return await restore_profile_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Fake Post X"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}fakex [opsi] (teks)'), cell('Gambar postingan X dari teks')],
                    [cell('reply orang'), cell('Pakai nama & foto profilnya')],
                    [cell('reply / kirim foto'), cell('Foto jadi media postingan')],
                    [cell('dark / dim / light'), cell('Tema')],
                    [cell(f'{prefix}fakex dark Alice Keren 🔥'), cell('Contoh')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Clone & Restore Profil"],
            table([
                [cell('Perintah'), cell('Keterangan')],
                [cell(f'{prefix}clone'), cell('Reply user untuk salin nama, bio & foto profil')],
                [cell(f'{prefix}restore'), cell('Kembalikan profil awal dari backup')],
                [cell('Backup'), cell('Otomatis di database; tidak ditimpa clone berulang')],
                [cell('Foto saat restore'), cell('Hanya foto hasil clone yang dihapus')],
                [cell('Clone versi lama'), cell('Tanpa backup tidak bisa dipulihkan otomatis')],
                [cell('Akun tujuan'), cell('Akun userbot yang menjalankan perintah')],
                [cell('Akses'), cell('Hanya pemilik akun userbot')],
                [cell('Username'), cell('Tidak diubah')],
                [cell('Foto tersembunyi'), cell('Dilewati; foto akunmu tidak diubah')],
                [cell('Penggunaan'), cell('Dengan persetujuan target, bukan untuk menipu')],
            ], bordered=True, striped=True),
        ),
        divider(),
        footer_table(),
    )
    button = ikb([
        [("Back", f"help_back({prev_page_num})", ButtonStyle.DANGER, "5258330865674494479")],
    ])
    if message_id:
        return await client.edit_rich_message(
            chat_id, message_id, rich, reply_markup=button
        )
    return await client.send_rich_message(chat_id, rich, reply_markup=button)