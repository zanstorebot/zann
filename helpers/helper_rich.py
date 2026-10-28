###################################################
""""
CREDITS : @aliceajako @synystercodes 

DILARANG KERAS HAPUS CREDIT ATAU MENGGANTINYA!!
NGAKU2 BOOLNYA PANAS 7 TURUNAN!!

Semua fungsi di bawah sudah tersedia otomatis lewat:
    from pyrogram.helpers import (
        heading, paragraph, divider, footer, math_expression, anchor,
        pull_quote, block_quote, code_block, list_item, rich_list,
        cell, table, details, photo_block, video_block, animation_block,
        audio_block, voice_block, document_block, button, button_row,
        buttons_grid, send_rich, RichMessageBuilder, Button,
    )
"""
###################################################

# =====================================================================
# 1. TEKS & JUDUL

# Paragraf teks biasa
paragraph("Halo, ini paragraf pertama di rich message.")

# Judul/heading â€” size 1 = paling besar, size 6 = paling kecil
heading("Judul Utama", 1)
heading("Sub Judul", 3)

# Catatan kaki, biasanya ditaruh paling bawah pesan
footer("Dikirim otomatis oleh bot.")

# Garis pemisah horizontal, tanpa argumen
divider()

# Rumus matematika format LaTeX
math_expression("E = mc^2")

# Penanda posisi tersembunyi (jarang dipakai, untuk link internal)
anchor("bagian-penting")


# =====================================================================
# 2. KUTIPAN

# Kutipan besar di tengah, credit = nama sumber (opsional)
pull_quote("Kesederhanaan adalah puncak dari kecanggihan.", "Leonardo da Vinci")

# Kutipan biasa (mirip <blockquote>), isinya BISA berupa beberapa block sekaligus
block_quote(
    paragraph("Ini isi kutipan, bisa lebih dari satu paragraf."),
    paragraph("Ini paragraf kedua di kutipan yang sama."),
    credit="Sumber Berita",
)

# =====================================================================
# 3. KODE

# Blok kode dengan syntax highlight, language=None untuk tanpa highlight
code_block("for i in range(5):\n    print(i)", "python")


# =====================================================================
# 4. LIST & CHECKLIST

# Satu item list biasa: label + isi (isi minimal 1 block, biasanya paragraph)
item1 = list_item("1.", paragraph("Item pertama"))
item2 = list_item("2.", paragraph("Item kedua"))

# Satu item checklist: label kosong + has_checkbox=True
todo1 = list_item("", paragraph("Beli susu"), has_checkbox=True, is_checked=False)
todo2 = list_item("", paragraph("Bayar listrik"), has_checkbox=True, is_checked=True)

# Gabungkan semua item jadi satu list utuh
rich_list(item1, item2)
rich_list(todo1, todo2)


# =====================================================================
# 5. TABEL

# Satu sel tabel. is_header=True -> teks otomatis tebal + ditandai header.
# colspan/rowspan buat gabung kolom/baris. align: left/center/right.
sel_a = cell("Fitur", is_header=True)
sel_b = cell("Status", is_header=True)
sel_c = cell("Auto Reply")
sel_d = cell("Aktif")
sel_total = cell("Total", colspan=2, align="center")

# Tabel dari list-of-list sel (baris demi baris)
table(
    [
        [sel_a, sel_b],
        [sel_c, sel_d],
    ],
    bordered=True,
    striped=True,
)


# =====================================================================
# 6. DETAILS (COLLAPSIBLE / BISA DIBUKA-TUTUP)

# summary = judul yang selalu terlihat, is_open=True kalau mau default terbuka
details(
    "Klik untuk lihat detail tambahan",
    paragraph("Ini isi yang baru terlihat setelah details dibuka."),
    is_open=False,
)

# =====================================================================
# 7. MEDIA (foto/video/animasi/audio/voice/dokumen)
# PENTING: semua fungsi media ini menerima file_id STRING langsung
# (tidak wajib objek Photo/Video asli) -- jadi gampang diganti-ganti
# lewat database tanpa proses tambahan apa pun.

photo_block("AgACAgUAAxkDAA...contoh_file_id_foto", has_spoiler=False)

video_block("BAACAgUAAxkDAA...contoh_file_id_video")

animation_block("CgACAgUAAxkDAA...contoh_file_id_gif", has_spoiler=True)

audio_block("CQACAgUAAxkDAA...contoh_file_id_audio")

voice_block("DQACAgUAAxkDAA...contoh_file_id_voice")

document_block("BQACAgUAAxkDAA...contoh_file_id_dokumen")

# Kalau sumbernya dari pesan yang di-reply user, bisa langsung pakai objek asli:
# photo_block(message.reply_to_message.photo)


# =====================================================================
# 8. TOMBOL (BUTTON)

# Satu tombol: text, data (callback) atau url, style (primary/secondary/success/danger)
btn_ya = button("Ya", callback_data="setuju_ya", style="success")
btn_tidak = button("Tidak", callback_data="setuju_tidak", style="danger")
btn_web = button("Website", url="https://example.com")

# Satu baris tombol (beberapa tombol sejajar)
button_row(btn_ya, btn_tidak)

# Beberapa baris tombol sekaligus
buttons_grid([
    [btn_ya, btn_tidak],
    [btn_web],
])


# =====================================================================
# 9. GAYA FUNGSI LEPASAN kirim semua block sekaligus

async def contoh_kirim_gaya_fungsi(client, chat_id):
    await send_rich(
        client,
        chat_id,
        heading("Judul Pesan", 1),
        paragraph("Ini paragraf pembuka."),
        divider(),
        photo_block("AgACAgUAAxkDAA...contoh_file_id"),
        table([
            [cell("Plan", is_header=True), cell("Harga", is_header=True)],
            [cell("Basic"), cell("Rp 10.000")],
            [cell("Pro"), cell("Rp 25.000")],
        ]),
        button_row(button("Beli Sekarang", callback_data="beli")),
    )


# =====================================================================
# 10. GAYA FLUENT BUILDER dirantai (chained), hasil akhir sama saja

async def contoh_kirim_gaya_builder(client, chat_id):
    rich = (
        RichMessageBuilder()
        .heading("Judul Pesan", 1)
        .paragraph("Ini paragraf pembuka.")
        .divider()
        .photo("AgACAgUAAxkDAA...contoh_file_id")
        .table([
            [cell("Plan", is_header=True), cell("Harga", is_header=True)],
            [cell("Basic"), cell("Rp 10.000")],
            [cell("Pro"), cell("Rp 25.000")],
        ])
        .button_row(button("Beli Sekarang", callback_data="beli"))
        .build()
    )
    await client.send_rich_message(chat_id=chat_id, rich_message=rich)