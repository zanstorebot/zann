######################################################
# UPDATES PAYMENT GATEWAY CASAKU.ID

# ©CREDITS: @ALICEDEVSCODES as DEVA | @MELIN -> TEMEN GUA 
# DIKATA COPAS LU BABJ ANJING ASYU
# NGAKU NGAKH BOOL NYA PANAS 7 TURUNAN 

######################################################


import asyncio
import os
import time
import traceback
from datetime import datetime, timedelta

import httpx
import qrcode
from dateutil.relativedelta import relativedelta
from pyrogram import filters, enums
from pyrogram.enums import ButtonStyle
from pyrogram.helpers import (send_rich,
    paragraph,
    heading,
    divider,
    footer,
    table,
    cell,
    ikb
)
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            KeyboardButton, ReplyKeyboardMarkup,
                            ReplyKeyboardRemove, InputRichMessage, 
                            RichTextMarked, RichTextTextMention,
                            RichTextBold, RichTextCustomEmoji)
from pytz import timezone

from clients import bot
from config import (AKSES_DEPLOY, CASAKU_BASE_URL, CASAKU_LICENSE_KEY,
                    CASAKU_PACKAGE_IDS, CASAKU_QRIS_ID, LOG_SELLER, OWNER_ID)
from database import dB
from helpers import ButtonUtils, Emoji, emo, Message
from logs import logger

transactions = {}
waktu_jkt = timezone("Asia/Jakarta")

PRICES = {
    "basic": 50000,
    "pro": 10000,
}
QRIS_EXPIRE_MINUTES = 10
POLL_INTERVAL = 4

_http_client = None


class CasakuError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")

    @property
    def user_message(self):
        if self.status == 403:
            return "Sistem pembayaran sedang offline. Silakan coba lagi beberapa menit lagi."
        if self.status == 429:
            return "Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi."
        if self.status in (401, 0, 408):
            return "Sistem pembayaran sedang bermasalah. Silakan hubungi admin."
        return "Terjadi kesalahan pada pembayaran. Silakan coba lagi."

    @property
    def admin_message(self):
        if self.status == 401:
            return "License Key Casaku tidak valid / belum diisi (401)."
        if self.status == 403:
            return "Listener Casaku OFFLINE (403). Casaku Belum Premium."
        if self.status == 429:
            return "Rate limit Casaku tercapai (429)."
        return str(self)


def _get_http():
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=CASAKU_BASE_URL.rstrip("/"),
            headers={
                "x-license-key": CASAKU_LICENSE_KEY,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(15.0),
        )
    return _http_client


async def _request(method, path, **kwargs):
    if not CASAKU_LICENSE_KEY:
        raise CasakuError(401, "CASAKU_LICENSE_KEY belum diisi")
    try:
        resp = await _get_http().request(method, path, **kwargs)
    except httpx.TimeoutException:
        raise CasakuError(408, "Timeout menghubungi Casaku")
    except httpx.HTTPError as e:
        raise CasakuError(0, f"Koneksi ke Casaku gagal: {e}")

    try:
        body = resp.json()
    except ValueError:
        body = {}

    if resp.status_code != 200 or body.get("status", 200) != 200:
        code = resp.status_code if resp.status_code != 200 else body.get("status", 500)
        raise CasakuError(code, body.get("message") or resp.text[:200])
    return body.get("data", body)


async def generate_qris(amount, expired_minutes=QRIS_EXPIRE_MINUTES):
    payload = {
        "id": CASAKU_QRIS_ID,
        "amount": int(amount),
        "useUniqueCode": True,
        "packageids": [p.strip() for p in CASAKU_PACKAGE_IDS.split(",") if p.strip()],
        "expiredInMinutes": expired_minutes,
    }
    return await _request("POST", "/api/generate/qris", json=payload)


async def check_status(transaction_id):
    return await _request(
        "POST", "/api/generate/check-status", json={"transactionId": transaction_id}
    )


async def cancel_transaction(transaction_id):
    return await _request(
        "POST", "/api/generate/cancel-status", json={"transactionId": transaction_id}
    )


async def make_qr_image(qr_string, path):
    await asyncio.to_thread(lambda: qrcode.make(qr_string).save(path))
    return path


async def wait_for_payment(transaction_id, expired_minutes, is_active):
    deadline = time.monotonic() + (expired_minutes + 1) * 60
    errors = 0
    while time.monotonic() < deadline:
        await asyncio.sleep(POLL_INTERVAL)
        if not is_active():
            return "cancelled"
        try:
            data = await check_status(transaction_id)
            errors = 0
        except CasakuError as e:
            errors += 1
            if e.status == 401 or errors >= 5:
                raise
            if e.status == 429:
                await asyncio.sleep(10)
            continue

        status = data.get("status")
        if status in ("paid", "cancel", "expired"):
            return status
    return "expired"


def normalize_plan(plan):
    return "basic" if str(plan).lower() == "basic" else "pro"


def plan_label(plan):
    return "Basic" if normalize_plan(plan) == "basic" else "Pro"


def get_price(plan, month):
    return PRICES[normalize_plan(plan)] * month


async def notify_admin(client, text):
    try:
        await client.send_message(LOG_SELLER, f"<b>⚠️ Casaku:</b> {text}")
    except Exception:
        pass


async def add_transaction(user_id, month, plan):
    await dB.set_var(user_id, "plan", plan)
    expired = await dB.get_expired_date(user_id)
    if not expired:
        now = datetime.now(waktu_jkt)
        expired = now + relativedelta(months=month)
        await dB.set_expired_date(user_id, expired)


def _remove_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


async def _delete_qr_message(client, chat_id, message_id):
    try:
        await client.delete_messages(chat_id=chat_id, message_ids=message_id)
    except Exception:
        pass


async def user_aggre(client, callback_query):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    buttons = ButtonUtils.chose_plan()
    loading = await client.send_message(
        user_id,
        "<b>Please wait...</b>",
        reply_markup=ReplyKeyboardRemove(),
    )
    await loading.delete()
    try:
        await callback_query.message.delete()
    except Exception:
        pass

    return await send_rich(
        client,
        user_id,
        heading(
            [
                emo(5298711594140724699, "💎"),
                (" Userbot Ultra Premium"),
            ],
            3,
        ),      
        divider(),      
        table(
            [
                [
                    cell(
                        [
                            emo(5298711594140724699, "💎"),
                            RichTextBold(" ULTRA PREMIUM"),
                        ],
                        is_header=True,
                    )
                ],
                [
                    cell(
                        [
                            emo(6240210026477130678, "🎮"),
                            " 76 Fitur",
                        ]
                    )
                ],
                [
                    cell(
                        [
                            emo(5244862548313925213, "✅"),
                            " Curi Foto Timer",
                        ]
                    )
                ],
                [
                    cell(
                        [
                            emo(6114136544312824398, "✅"),
                            " Curi Media CH Private",
                        ]
                    )
                ],
                [
                    cell(
                        [
                            emo(5359726582447487916, "✅"),
                            " Fitur AI Ready",
                        ]
                    )
                ],
                [
                    cell(
                        [
                            emo(5170574646478635764, "💰"),
                            " Rp10.000",
                        ]
                    )
                ],
            ],
        ),        
        divider(),      
        table(
            [
                [
                    cell(
                        "AliceDevs Core v3.14 ⚡",
                        align="center",
                        is_header=True,
                    )
                ],
            ],
            bordered=True,
            striped=True,
            compact=True,
        ),      
        footer(
            [
                emo(5447644880824181073, "💎"),
                (
                    " Pilih plan terlebih dahulu sebelum pembayaran. "
                    "Daftar fitur dapat berubah sesuai pengembangan developer."
                ),
            ]
        ), 
      reply_markup=buttons,
    )
    
  

async def chose_plan(client, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()
    user_id = callback_query.from_user.id
    plan = str(callback_query.data.split()[1])
    buttons = ButtonUtils.plus_minus(0, 0, plan)
    return await client.send_message(
        user_id,
        Message.TEXT_PAYMENT(0, 0, 0, plan_label(plan), 0),
        disable_web_page_preview=True,
        reply_markup=buttons,
    )


async def kurang_tambah(client, callback_query):
    try:
        data = callback_query.data.split()
        QUERY = data[0]
        BULAN = int(data[1])
        PLAN = str(data[-1])

        if QUERY == "kurang":
            if BULAN > 1:
                BULAN -= 1
        elif QUERY == "tambah":
            if BULAN < 12:
                BULAN += 1

        HARGA = PRICES[normalize_plan(PLAN)]
        DISKON = 0
        TOTAL_HARGA = get_price(PLAN, BULAN) - DISKON

        buttons = ButtonUtils.plus_minus(BULAN, TOTAL_HARGA, PLAN)
        await callback_query.edit_message_text(
            Message.TEXT_PAYMENT(HARGA, TOTAL_HARGA, BULAN, plan_label(PLAN), DISKON),
            disable_web_page_preview=True,
            reply_markup=buttons,
        )
    except Exception:
        logger.error(f"ERROR kurang_tambah: {traceback.format_exc()}")


async def confirm_pay(client: Message, callback_query):
    await callback_query.answer()
    data = callback_query.data.split()
    user_id = callback_query.from_user.id

    plan = str(data[-1])
    PLAN = plan_label(plan)
    unit = PRICES[normalize_plan(plan)]

    try:
        val = int(data[1])
    except (IndexError, ValueError):
        val = 0
    # data[1] berisi TOTAL HARGA (mis. 10000), bukan jumlah bulan
    month = val // unit if val >= unit else val

    await callback_query.message.delete()

    if not 1 <= month <= 12:
        return await client.send_message(user_id, "<b>Jumlah bulan tidak valid.</b>")
    amount = get_price(plan, month)
    if amount <= 0:
        return await client.send_message(user_id, "<b>The price cannot be 0.</b>")
    if user_id in transactions:
        return await callback_query.message.reply(
            "**__📑 You still have a pending transaction.__**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Cancel", callback_data="batal_payment")]]
            ),
        )

    loading = await callback_query.message.reply(
        "<blockquote><b> Loading Your QRIS...</b></blockquote>"
    )
    qris_path = None
    tid = None
    bukti_task = None
    try:
        try:
            trx = await generate_qris(amount, QRIS_EXPIRE_MINUTES)
        except CasakuError as e:
            logger.error(f"Casaku generate error: {e}")
            await loading.delete()
            if e.status in (401, 403, 429, 0, 408):
                await notify_admin(client, e.admin_message)
            return await client.send_message(user_id, f"<b>❌ {e.user_message}</b>")

        tid = trx["transactionId"]
        total_price = int(trx["totalAmount"])
        expired_min = int(trx.get("expiredInMinutes", QRIS_EXPIRE_MINUTES))
        payment_url = trx.get("payment_url")
        item_name = f"Userbot Premium {month} Bulan"

        qris_path = f"qris_{user_id}_{tid[:8]}.png"
        await make_qr_image(trx["qr_string"], qris_path)

        now = datetime.now(waktu_jkt)
        expire_time = now + timedelta(minutes=expired_min)

        buttons = []
        if payment_url:
            buttons.append(
                [InlineKeyboardButton("📑 Buka Halaman Pembayaran", url=payment_url)]
            )
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="batal_payment")])

        await loading.delete()
        sent_msg = await callback_query.message.reply_photo(
            qris_path,
            caption=f"""
<b>💳 SCAN QRIS UNTUK MEMBELI</b>
<blockquote><b>
📦 Item: <code>{item_name}</code>
💵 Harga: <code>{Message.format_rupiah(amount)}</code>
💰 Total Bayar: <code>{Message.format_rupiah(total_price)}</code>
⏰ Expired Pembayaran: <code>{expire_time.strftime('%H:%M')}</code>

⚠️ Pembayaran terdeteksi otomatis.
</b></blockquote>
<blockquote>© Auto Payment By: @{client.me.username}</blockquote>
""",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        # Daftarkan transaksi dulu, supaya tombol Cancel langsung berfungsi
        transactions[user_id] = {
            "transaction_id": tid,
            "qris_path": qris_path,
            "message_id": sent_msg.id,
            "chat_id": callback_query.message.chat.id,
        }

        def still_active():
            return transactions.get(user_id, {}).get("transaction_id") == tid

        # Minta bukti di background, supaya polling tidak tertahan
        async def minta_bukti():
            try:
                bukti = await client.ask(
                    user_id,
                    "<blockquote><b>🧾 Silakan kirimkan bukti pembayaran yang sudah Anda lakukan</b></blockquote>",
                    filters=filters.photo,
                    timeout=expired_min * 60,
                )
                copied = await bukti.copy(
                    LOG_SELLER,
                    caption=(
                        f"""<blockquote><b>🧾 Bukti pembayaran</b>\n\n
                        User: <code>{user_id}</code>\n
                        Plan: {PLAN}\n
                        Harga: {Message.format_rupiah(amount)}</b></blockquote>"""
                    ),
                    reply_markup=ikb(
                        [
                            [
                                (" Give Access", f"ubot {user_id} {client.me.username} {plan} {month}", ButtonStyle.SUCCESS, "5307843983102204243"),
                            ],
                        ]
                    ),
                )
                # supaya admin bisa membalas pembeli lewat outgoing_reply
                await dB.set_var(copied.id, f"FORWARD_{copied.id}", user_id)
                await client.send_message(
                    user_id,
                    "<blockquote><b>✅ Bukti pembayaran terkirim, tunggu admin memproses.</b></blockquote>",
                )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error kirim bukti: {e}")
            

        bukti_task = asyncio.create_task(minta_bukti())

        # Polling status pembayaran ke Casaku
        try:
            status = await wait_for_payment(tid, expired_min, still_active)
        except CasakuError as e:
            bukti_task.cancel()
            logger.error(f"Casaku polling error: {e}")
            await notify_admin(client, f"Polling gagal untuk {tid}: {e.admin_message}")
            if still_active():
                await _delete_qr_message(client, sent_msg.chat.id, sent_msg.id)
                del transactions[user_id]
            return await client.send_message(
                user_id,
                "<b>⚠️ Gagal mengecek pembayaran. Jika sudah membayar, hubungi admin dengan menyertakan bukti transfer.</b>",
            )

        bukti_task.cancel()  # pembayaran selesai/batal/expired, berhenti menunggu foto

        if status == "cancelled":
            return
          
        if still_active():
            del transactions[user_id]
        await _delete_qr_message(client, sent_msg.chat.id, sent_msg.id)

        if status == "paid":
            await client.send_message(
                LOG_SELLER,
                f"""
<b>📝「 Payment Successfully 」</b>

<blockquote><b><i>👤 User Name: <code>{callback_query.from_user.first_name}</code>
🆔 User ID: <code>{str(user_id)[:3]}######</code>
📦 Item: <code>{item_name}</code>
💵 Price: <code>{Message.format_rupiah(amount)}</code>
💰 Paid: <code>{Message.format_rupiah(total_price)}</code>
🧾 Trx: <code>{tid}</code>
📅 Date: <code>{now.strftime('%d-%m-%Y')}</code>
⏰ Time: <code>{datetime.now(waktu_jkt).strftime('%H:%M')}</code></i></b></blockquote>

<blockquote>© Auto Payment @{client.me.username}</blockquote>
""",
            )
            await add_transaction(user_id, month, plan)
            if user_id not in AKSES_DEPLOY:
                AKSES_DEPLOY.append(user_id)
            await client.send_message(
                user_id,
                "<b><i>✅ Payment successful.\nClick the button below to create your UserBot.</i></b>",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("✨ Mulai Buat Userbot")]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                ),
            )
        else:
            await client.send_message(
                user_id,
                "<b>⌛ Waktu pembayaran habis atau transaksi dibatalkan. Silakan buat transaksi baru.</b>",
            )

    except Exception:
        logger.error(f"ERROR confirm_pay: {traceback.format_exc()}")
        if bukti_task:            # <-- tambahkan ini
            bukti_task.cancel()
        if transactions.get(user_id, {}).get("transaction_id") == tid:
            transactions.pop(user_id, None)
        _remove_file(qris_path)
        return await client.send_message(
            user_id, "<b>An error occurred, please try again.</b>"
        )


async def cancel_payment(client, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.answer()

    tx = transactions.pop(user_id, None)
    if not tx:
        return await callback_query.message.reply(
            "**__❌ Tidak Ada Transaksi Yang Aktif__**"
        )

    _remove_file(tx.get("qris_path"))
    try:
        await cancel_transaction(tx["transaction_id"])
    except CasakuError as e:
        logger.warning(f"Cancel Casaku gagal: {e}")
    await _delete_qr_message(client, tx["chat_id"], tx["message_id"])

    await callback_query.message.reply(
        "**__📑 Transaksi Berhasil Dibatalkan.__**",
        reply_markup=ButtonUtils.start_menu(user_id),
    )


async def kasih_vip(client, callback_query):
    user_ids = int(callback_query.data.split()[1])
    msg = """<b>✅ Pembelian Channel VIP Sukses</b>

Link VIP: <spoiler>cari dipencarian: @satorugojovip | satorugojovip.t.me | t.me/satorugojovip</spoiler>
Cara melihat medianya:
Klik profile channel diatas, lalu akan terlihat semua media.
Atau bisa klik pin pesan yang sudah tersemat
<blockquote><b>Jangan lupa beli userbot dengan fitur curi foto & video sekali liat
Untuk penjelasan detailnya silahkan klik tombol Contoh Kelebihan Userbot</b></blockquote>
✨ Selamat menikmat"""

    buttons = ikb(
        [
            [
                ("💻 Beli Userbot", "https://t.me/devfavbot?start=kontol", "url", ButtonStyle.PRIMARY),
                ("✨ Kelebihan Userbot", "https://t.me/devspaybot?start=kontol", "url", ButtonStyle.SUCCESS),
            ],
        ]
    )
    await client.send_message(
        user_ids,
        msg,
        reply_markup=buttons,
        effect_id=5104841245755180586,
    )
    await callback_query.message.edit("**✅ Pesan telah di kirim**")


async def kasih_ubot(client, callback_query):
    await callback_query.answer()
    data = callback_query.data.split()
    user_ids = int(data[1])
    plan = str(data[3])
    month = int(data[4])
    PLAN = plan_label(plan)

    await add_transaction(user_ids, month, plan)
    if user_ids not in AKSES_DEPLOY:
        AKSES_DEPLOY.append(user_ids)

    await client.send_message(
        user_ids,
        f"<blockquote><b>✅ Akses userbot premium sudah diberikan! Silahkan klik tombol di bawah untuk membuat userbot kamu.</b></blockquote>",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("✨ Mulai Buat Userbot")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    await callback_query.message.edit(
        f"<b>✅ Akses Userbot ({month} bulan) telah diberikan ke user <code>{user_ids}</code>.</b>"
    )


async def qris_cmd(client, message):
    em = Emoji(client)
    await em.get()

    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return await message.reply(
            f"{em.gagal}**Sorry, this feature is only for the Owner.**"
        )

    if user_id in transactions:
        return await message.reply(
            f"""
<b><i>{em.gagal}You still have an ongoing transaction.
{em.warn}You can cancel it using <code>.cancelpay</code>.</i></b>
"""
        )

    args = message.text.split(maxsplit=1)
    try:
        amount_str, description = args[1].split(",", maxsplit=1)
        amount = int(amount_str.strip())
        description = description.strip()
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        return await message.reply(
            f"{em.gagal}**Incorrect format. Use:** <code>.pay amount, description</code>"
        )

    loading = await message.reply(f"{em.proses}**Prosesing..**")
    qris_path = None
    tid = None
    try:
        try:
            trx = await generate_qris(amount, QRIS_EXPIRE_MINUTES)
        except CasakuError as e:
            await loading.delete()
            return await message.reply(f"{em.gagal}**{e.admin_message}**")

        tid = trx["transactionId"]
        total_amount = int(trx["totalAmount"])
        expired_min = int(trx.get("expiredInMinutes", QRIS_EXPIRE_MINUTES))
        formatted_time = (
            datetime.now(waktu_jkt) + timedelta(minutes=expired_min)
        ).strftime("%H:%M")

        qris_path = f"qris_{user_id}_{tid[:8]}.png"
        await make_qr_image(trx["qr_string"], qris_path)

        await loading.delete()
        sent_message = await message.reply_photo(
            qris_path,
            caption=f"""
<b>📃「 Waiting Payment 」</b>

<blockquote><b><i>{em.profil}Item: <code>{description}</code>
{em.net}Price: <code>Rp{amount:,}</code>
{em.speed}Total Payment: <code>Rp{total_amount:,}</code>
{em.warn}Expiration Time: <code>{formatted_time}</code>

Please scan the QRIS above to complete the payment.
If you encounter any issues, contact <a href='tg://user?id={OWNER_ID}'>ADMIN</a>
Type <code>.cancelpay</code> to cancel the transaction.</i></b></blockquote>

<blockquote>© Auto Payment @{bot.me.username}</blockquote>
""",
        )
        _remove_file(qris_path)

        transactions[user_id] = {
            "transaction_id": tid,
            "qris_path": qris_path,
            "message_id": sent_message.id,
            "chat_id": message.chat.id,
        }

        def still_active():
            return transactions.get(user_id, {}).get("transaction_id") == tid

        try:
            status = await wait_for_payment(tid, expired_min, still_active)
        except CasakuError as e:
            if still_active():
                del transactions[user_id]
            await _delete_qr_message(client, message.chat.id, sent_message.id)
            return await message.reply(f"{em.gagal}**{e.admin_message}**")

        if status == "cancelled":
            return

        if still_active():
            del transactions[user_id]
        await _delete_qr_message(client, message.chat.id, sent_message.id)

        if status == "paid":
            await message.reply(
                f"""
<blockquote><b><i>{em.sukses}Payment received successfully!

{em.profil}Item: <code>{description}</code>
{em.net}Price: <code>Rp{amount:,}</code>
{em.speed}Total Paid: <code>Rp{total_amount:,}</code></i></b></blockquote>
"""
            )
        else:
            await message.reply(
                f"{em.gagal}**Transaction canceled due to expiration.**"
            )
    except Exception:
        logger.error(f"ERROR qris_cmd: {traceback.format_exc()}")
        if transactions.get(user_id, {}).get("transaction_id") == tid:
            transactions.pop(user_id, None)
        _remove_file(qris_path)
        await message.reply(f"{em.gagal}**An error occurred, please try again.**")


async def cancelpay_cmd(client, message):
    em = Emoji(client)
    await em.get()

    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return await message.reply(
            f"{em.gagal}**Sorry, this feature is only for the Owner.**"
        )

    tx = transactions.pop(user_id, None)
    if not tx:
        return await message.reply(
            f"{em.warn}**There is no active transaction to cancel.**"
        )

    _remove_file(tx.get("qris_path"))
    try:
        await cancel_transaction(tx["transaction_id"])
    except CasakuError as e:
        logger.warning(f"Cancel Casaku gagal: {e}")
    await _delete_qr_message(client, tx["chat_id"], tx["message_id"])

    return await message.reply(
        f"{em.sukses}**Transaction has been successfully canceled.**"
    )