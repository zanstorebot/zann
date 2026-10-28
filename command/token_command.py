import asyncio
import importlib
import json
import traceback
from datetime import datetime, timedelta

import hydrogram
from dateutil.relativedelta import relativedelta
from pyrogram.enums import ButtonStyle
from pyrogram.helpers import ikb
from pyrogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                            ReplyKeyboardRemove)
from pytz import timezone

import config
from clients import UserBot, bot, alice
from config import API_HASH, API_ID, LOG_SELLER, WAJIB_JOIN
from database import dB
from helpers import ButtonUtils, TokenReferal, Tools, no_trigger, stoped_ubot
from logs import logger
from plugins import PLUGINS


async def referal_command(client, message):
    msg = """
<b>📢 SISTEM REFERRAL</b>

<b>Apa itu Kode Referral?</b>
Kode Referral kamu berfungsi untuk mengajak pengguna lain menggunakan bot ini. Dan jika kode referral kamu sudah digunakan 2 kali, maka kamu bisa mendapatkan keuntungan:

• Menambahkan masa aktif userbot selama 1 bulan
• Memasang userbot gratis menggunakan akun kamu yang lain

<b>Cara menggunakan:</b>
1. Bagikan kode referralmu kepada teman
2. Minta mereka mendaftar menggunakan kode referralmu
3. Cek status dengan /status di bot ini

<b>Tips:</b>
Bagikan referral kamu di grup, channel, atau story untuk mendapatkan pengguna baru lebih cepat!
"""

    buttons = ikb(
        [
            [("🎁 Klaim Reward Referral", "claim_referral", ButtonStyle.SUCCESS, "5258330865674494479")],
            [("📊 Status Referral", "status_referral", ButtonStyle.PRIMARY, "5258330865674494479")],
        ]
    )
    return await message.reply(msg, reply_markup=buttons)


async def tools_referral(client, query):
    tokenref = await TokenReferal.create()
    user_id = query.from_user.id
    if str(user_id) not in tokenref.users:
        await tokenref.generate_referral_code(str(user_id))
    data = query.data
    if data == "claim_referral":
        stats = await tokenref.get_referral_stats(str(user_id))
        count = stats["invited_users_count"]
        if count >= 2:
            buttons = ikb(
                [[("Tambah Expired", "use_expired"), ("Deploy Userbot", "use_userbot")]]
            )
            msg = """
<b>🎉 SELAMAT! 🎉</b>

Kode referral kamu telah berhasil digunakan oleh 2 pengguna!
Sebagai penghargaan atas kontribusi kamu dalam mengembangkan userbot kami, kamu berhak mendapatkan salah satu hadiah berikut:

- <b>Tambah Expired</b> - Perpanjang masa aktif userbot kamu selama 1 bulan
- <b>Deploy Userbot</b> - Pasang userbot gratis di akun Telegram lain yang kamu miliki

Silahkan pilih salah satu reward yang kamu inginkan dengan menekan tombol di bawah.
"""
            return await query.edit_message_text(msg, reply_markup=buttons)
        else:
            text = f"<b>Kamu belum memenuhi syarat untuk mengklaim Referral!!\nJumlah pengguna Referral kamu adalah: </b>{count} ."
            buttons = ikb([[("❌ Tutup", "buttonclose")]])
            return await query.edit_message_text(text, reply_markup=buttons)
    elif data == "status_referral":
        stats = await tokenref.get_referral_stats(str(user_id))
        koderef = stats["referral_code"]
        date = tokenref.referrals[koderef].get("created_at")
        dates = Tools.jakartaTime(date) if date else "-"
        msg = f"""
<b>📊 Status Referral</b>

<b>Kode Referral:</b> <code>{stats['referral_code']}</code>
<b>Jumlah pengguna:</b> <code>{stats['invited_users_count']}</code>
<b>Dibuat:</b> <code>{dates}</code>
"""
        buttons = ikb([[("❌ Tutup", "buttonclose", ButtonStyle.DANGER, "5258330865674494479")]])
        return await query.edit_message_text(msg, reply_markup=buttons)


async def use_referral(client, query):
    tokenref = await TokenReferal.create()
    user_id = query.from_user.id
    data = query.data
    if data == "use_expired":
        if user_id not in alice._get_my_id:
            buttons = ikb([[("Deploy Userbot", "use_userbot")]])
            return await query.edit_message_text(
                "<b>Maaf, kamu tidak bisa menambahkan expired ke akun ini karena akun ini belum memasang userbot. Silahkan pilih tombol Deploy Userbot!!</b>",
                reply_markup=buttons,
            )

        expired_dt = await dB.get_expired_date(user_id)
        if not expired_dt:
            return await query.edit_message_text("Gagal mendapatkan data expired user.")

        now1 = datetime.now(expired_dt.tzinfo or timezone(timedelta(hours=7)))
        total_days = (expired_dt - now1).days

        now2 = datetime.now(timezone(timedelta(hours=7)))
        expired1 = now2 + relativedelta(months=1)
        expired2 = expired1 + timedelta(days=total_days)

        await dB.set_expired_date(user_id, expired2)
        await tokenref.generate_referral_code(str(user_id))
        new_exp = await dB.get_expired_date(user_id)

        status_referal = await tokenref.get_referral_stats(str(user_id))
        habis = (
            new_exp.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M")
            if new_exp
            else "None"
        )

        msg = f"""
<b>🎉 SELAMAT! 🎉</b>

Masa aktif kamu berhasil ditambahkan dan kode Referral kamu telah diperbarui.

<blockquote><b>Tanggal Kedaluwarsa:</b> <code>{habis}</code>
<b>Token:</b> <code>{status_referal.get('token', '-')}</code>
<b>Kode Referral:</b> <code>{status_referal.get('referral_code', '-')}</code>
<b>Pengguna Referral:</b> <code>{status_referal.get('invited_users_count', 0)}</code></blockquote>
"""
        buttons = ikb([[("❌ Tutup", "buttonclose", ButtonStyle.DANGER, "5258330865674494479")]])
        return await query.edit_message_text(msg, reply_markup=buttons)

    elif data == "use_userbot":
        stats = await tokenref.get_referral_stats(str(user_id))
        count = stats["invited_users_count"]
        if count < 2:
            text = f"<b>Kamu belum memenuhi syarat untuk mengklaim Referral!!\nJumlah pengguna Referral kamu adalah: {count} .</b>"
            buttons = ikb([[("❌ Tutup", "buttonclose", ButtonStyle.DANGER, "5258330865674494479")]])
            return await query.edit_message_text(text, reply_markup=buttons)
        await query.message.delete()
        try:
            target_akses = await client.ask(
                user_id,
                "<b>Silahkan kirim username atau id pengguna untuk diberikan akses memasang userbot dan pastikan akun tersebut telah men-start bot ini!! atau ketik /cancel untuk membatalkan.</b>",
                timeout=300,
            )
            if target_akses.text in ["/cancel", "/start"]:
                return await client.send_message(user_id, "<b>Proses dibatalkan!!</b>")
            target = target_akses.text
            try:
                userid = (await client.get_users(target)).id
                mention = (await client.get_users(target)).mention
            except Exception:
                target_akses = await client.ask(
                    user_id,
                    "<b>Mohon buka akun tersebut dan start bot ini, lalu kirimkan ulang username atau id akun!! atau ketik /cancel untuk membatalkan.</b>",
                    timeout=300,
                )
                userid = (await client.get_users(target)).id
                mention = (await client.get_users(target)).mention
        except asyncio.TimeoutError:
            return await client.send_message(
                user_id, "<b>Waktu habis dan proses dibatalkan!!</b>"
            )
        config.AKSES_DEPLOY.append(userid)
        msg = f"""
<b>🎉 SELAMAT! 🎉</b>

Kamu berhasil meng-klaim Referral dan kode Referral kamu telah diperbarui.

Akun {mention} berhasil diberikan akses memasang userbot. Silahkan buka akun tersebut untuk melanjutkan pemasangan userbot.

<b>Kode Referral:</b> <code>{status_referal['referral_code']}</code>
<b>Pengguna Referral:</b> <code>{status_referal['invited_users_count']}</code></blockquote>
"""
        buttons = ikb([[("❌ Tutup", "buttonclose", ButtonStyle.DANGER, "5258330865674494479")]])
        return await query.edit_message_text(msg, reply_markup=buttons)


async def token_cmd(client, message):
    msg = """
<b>🔑 SISTEM TOKEN</b>

<b>Apa itu Token?</b>
Token kamu berfungsi untuk mengklaim garansi ubot dalam kondisi:
• Jika kamu ingin berpindah akun Telegram
• Jika akunmu dibanned oleh pihak Telegram
• Jika kamu perlu menginstall ulang userbot

<b>Perhatian:</b>
• Setiap token memiliki batas penggunaan maksimal 3 kali
• Token hanya bisa digunakan oleh pemiliknya
• Simpan token kamu dengan aman, jangan dibagikan

<b>Cara Kerja:</b>
Token berperan sebagai kunci akses untuk memindahkan layanan userbot dari satu akun ke akun lainnya tanpa harus membayar ulang.

<b>PENTING:</b> Mohon simpan Token kamu dengan aman!
"""

    buttons = ikb(
        [[("🔑 Gunakan Token", "use_token", ButtonStyle.SUCCESS, "5258330865674494479")], [("🔄 Revoke Token", "revoke_token", ButtonStyle.PRIMARY, "5258330865674494479")]]
    )
    return await message.reply(msg, reply_markup=buttons)


async def migrate_data(olduser: int, newuser: int):
    plan = await dB.get_var(olduser, "plan")
    if plan:
        await dB.set_var(newuser, "plan", plan)
    prefix = await dB.get_pref(olduser)
    if prefix:
        await dB.set_pref(newuser, prefix)
    cek_log = await dB.get_var(olduser, "GRUPLOG")
    if cek_log:
        await dB.remove_var(olduser, "GRUPLOG")
    all_var = await dB.all_var(olduser)
    if all_var:
        for key, value in all_var.items():
            parsed_value = json.loads(value)
            await dB.set_var(newuser, key, parsed_value, query="vars")

    all_notes = await dB.all_var(olduser, query="notes")
    if all_notes:
        for key, value in all_notes.items():
            parsed_value = json.loads(value)
            await dB.set_var(newuser, key, parsed_value, query="notes")

    all_filters = await dB.all_var(olduser, query="filter")
    if all_filters:
        for key, value in all_filters.items():
            parsed_value = json.loads(value)
            await dB.set_var(newuser, key, parsed_value, query="filter")

    return True


async def tools_token(client, query):
    tokenref = await TokenReferal.create()
    data = query.data
    user_id = query.from_user.id
    if data == "use_token":
        await query.message.delete()
        try:
            token_ask = await client.ask(
                user_id,
                "<b>Silahkan kirim kan token yang kamu miliki, untuk dicek terlebih dahulu!! atau ketik /cancel untuk membatalkan proses.</b>",
                timeout=300,
            )
            if token_ask.text in ["/cancel", "/start"]:
                return await client.send_message(user_id, "<b>Proses dibatalkan!!</b>")
        except asyncio.TimeoutError:
            return await client.send_message(
                user_id, "<b>Waktu habis dan proses dibatalkan!!</b>"
            )
        token = token_ask.text
        status = await tokenref.check_token_usage(str(token))
        if status["valid"] == False:
            return await client.send_message(
                user_id,
                "<b>Token yang kamu kirimkan tidak valid, dan tidak bisa digunakan!!</b>",
            )
        mention = (await client.get_users(int(status["owner"]))).mention
        tanggal = status["created_at"]
        oldowner = status["owner"]
        history = ""
        for count, story in enumerate(status["usage_history"], 1):
            history += f"{count}.{Tools.jakartaTime(story['timestamp'])} | {story['description']}\n"
        msg = f"""
<blockquote><b>Data Token</b>

➡️ <b>Pemilik: {mention}</b>
➡️ <b>Token</b>: <code>{token}</code>
➡️ <b>Penggunaan</b>: <code>{status['usage_count']}</code>
➡️ <b>Maksimal digunakan</b>: <code>{status['max_usage']}</code>
➡️ <b>Sisa penggunaan</b>: <code>{status['remaining_usage']}</code>
➡️ <b>Riwayat penggunaan</b>:

{history}
➡️ <b>Tanggal Pembuatan</b>: <code>{Tools.jakartaTime(tanggal)}</code></blockquote>

<b>Apakah anda ingin menggunakan token untuk meng-klaim garansi atau berpindah akun untuk userbot ? Jika setuju balas `Ya` atau balas `Tidak` untuk membatalkan.</b>
"""
        mention0 = (await client.get_users(user_id)).mention
        try:
            await client.send_message(
                int(oldowner),
                f"<b>Pengguna {mention0} mencoba menggunakan token anda, Jika itu bukan anda Silahkan lakukan revoke token.</b>",
            )
        except Exception:
            pass
        try:
            waiting = await client.ask(user_id, msg, timeout=300)
        except asyncio.TimeoutError:
            return await client.send_message(
                user_id, "<b>Waktu habis dan proses dibatalkan!!</b>"
            )
        if waiting.text in ["Tidak", "tidak", "No", "no"]:
            return await client.send_message(user_id, "<b>Proses dibatalkan!!</b>")
        else:

            anu = ReplyKeyboardMarkup(
                [
                    [KeyboardButton(text="Kontak Saya", request_contact=True)],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            try:
                try:
                    phone = await client.ask(
                        user_id,
                        f"<blockquote><b>Silahkan klik tombol <u>Kontak Saya</u> untuk mengirimkan Nomor Telepon Telegram Anda.</b></blockquote>",
                        reply_markup=anu,
                    )
                    phone_number = phone.contact.phone_number
                except AttributeError:
                    try:
                        phone = await client.ask(
                            user_id,
                            f"<blockquote><b>Silahkan klik tombol <u>Kontak Saya</u> untuk mengirimkan Nomor Telepon Telegram Anda.</b></blockquote>",
                            reply_markup=anu,
                        )
                        phone_number = phone.contact.phone_number
                    except Exception:
                        return await bot.send_message(
                            user_id,
                            "<blockquote><b>PEA, punya mata dipake buat baca!! jangan BOKEP mulu.</b></blockquote>",
                            reply_markup=ButtonUtils.start_menu(is_admin=False),
                        )
                new_client = hydrogram.Client(
                    name=str(user_id),
                    api_id=API_ID,
                    api_hash=API_HASH,
                    in_memory=True,
                )
                await asyncio.sleep(2)
                get_otp = await client.send_message(
                    user_id,
                    f"<b><blockquote>Sedang Mengirim Kode OTP...</blockquote></b>",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await new_client.connect()
                try:
                    code = await new_client.send_code(phone_number.strip())
                except hydrogram.errors.exceptions.bad_request_400.ApiIdInvalid as AID:
                    await get_otp.delete()
                    return await client.send_message(user_id, AID)
                except (
                    hydrogram.errors.exceptions.bad_request_400.PhoneNumberInvalid
                ) as PNI:
                    await get_otp.delete()
                    return await client.send_message(user_id, PNI)
                except (
                    hydrogram.errors.exceptions.bad_request_400.PhoneNumberFlood
                ) as PNF:
                    await get_otp.delete()
                    return await client.send_message(user_id, PNF)
                except (
                    hydrogram.errors.exceptions.bad_request_400.PhoneNumberBanned
                ) as PNB:
                    await get_otp.delete()
                    return await client.send_message(user_id, PNB)
                except (
                    hydrogram.errors.exceptions.bad_request_400.PhoneNumberUnoccupied
                ) as PNU:
                    await get_otp.delete()
                    return await client.send_message(user_id, PNU)
                except Exception as error:
                    await get_otp.delete()
                    return await client.send_message(
                        user_id,
                        f"<b>ERROR:</b> {error}",
                        reply_markup=ButtonUtils.start_menu(is_admin=False),
                    )
                await get_otp.delete()
                otp = await client.ask(
                    user_id,
                    f"<b><blockquote>Silakan Periksa Kode OTP dari <a href=tg://openmessage?user_id=777000>Akun Telegram</a> Resmi. Kirim Kode OTP ke sini setelah membaca Format di bawah ini.</b>\n\nJika Kode OTP adalah <code>12345</code> Tolong <b>[ TAMBAHKAN SPASI ]</b> kirimkan Seperti ini <code>1 2 3 4 5</code>.</blockquote></b>",
                )
                if otp.text in no_trigger:
                    return await client.send_message(
                        user_id,
                        f"<blockquote><b>Proses di batalkan.</b></blockquote>",
                        reply_markup=ButtonUtils.start_menu(is_admin=False),
                    )
                otp_code = otp.text
                try:
                    await new_client.sign_in(
                        phone_number.strip(),
                        code.phone_code_hash,
                        phone_code=" ".join(str(otp_code)),
                    )
                except (
                    hydrogram.errors.exceptions.bad_request_400.PhoneCodeInvalid
                ) as PCI:
                    return await client.send_message(user_id, PCI)
                except (
                    hydrogram.errors.exceptions.bad_request_400.PhoneCodeExpired
                ) as PCE:
                    return await client.send_message(user_id, PCE)
                except hydrogram.errors.exceptions.bad_request_400.BadRequest as error:
                    return await client.send_message(
                        user_id,
                        f"<b>ERROR:</b> {error}",
                        reply_markup=ButtonUtils.start_menu(is_admin=False),
                    )
                except (
                    hydrogram.errors.exceptions.unauthorized_401.SessionPasswordNeeded
                ):
                    two_step_code = await client.ask(
                        user_id,
                        f"<b><blockquote>Akun anda Telah mengaktifkan Verifikasi Dua Langkah. Silahkan Kirimkan Passwordnya.</blockquote></b>",
                    )
                    if two_step_code.text in no_trigger:
                        return await client.send_message(
                            user_id,
                            f"<blockquote><b>Proses di batalkan.</b></blockquote>",
                            reply_markup=ButtonUtils.start_menu(is_admin=False),
                        )
                    new_code = two_step_code.text
                    try:
                        await new_client.check_password(new_code)
                        await dB.set_var(user_id, "PASSWORD", new_code)
                    except Exception as error:
                        return await client.send_message(
                            user_id,
                            f"<b>ERROR:</b> {error}",
                            reply_markup=ButtonUtils.start_menu(is_admin=False),
                        )
                session_string = await new_client.export_session_string()
                await new_client.disconnect()
                new_client.storage.session_string = session_string
                new_client.in_memory = False
                bot_msg = await client.send_message(
                    user_id,
                    f"<b><blockquote>Tunggu proses selama 1-5 menit...\nKami sedang menghidupkan Userbot Anda.</blockquote></b>",
                    disable_web_page_preview=True,
                )
                await asyncio.sleep(2)
                kn_client = UserBot(
                    name=str(user_id),
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=session_string,
                    in_memory=True,
                )
                expired_dt = await dB.get_expired_date(int(oldowner))
                now1 = datetime.now(expired_dt.tzinfo)
                total_days = (expired_dt - now1).days
                new_expired_date = datetime.now(expired_dt.tzinfo) + timedelta(
                    days=total_days
                )
                await dB.set_expired_date(user_id, new_expired_date)
                try:
                    await kn_client.start()
                except Exception as e:
                    logger.error(f"Error Client: {str(e)}")
                await dB.add_ubot(
                    user_id=int(kn_client.me.id),
                    session_string=session_string,
                )
                if not user_id == kn_client.me.id:
                    alice._ubot.remove(kn_client)
                    await dB.remove_ubot(kn_client.me.id)
                    await kn_client.log_out()
                    return await bot_msg.edit(
                        f"<blockquote><b>Gunakan akun anda sendiri, bukan orang lain!!</b></blockquote>"
                    )
                _, new_ref = await tokenref.transfer_account(
                    token=token,
                    new_user_id=str(kn_client.me.id),
                    new_phone=phone_number.strip(),
                )
                await migrate_data(int(oldowner), kn_client.me.id)
                await stoped_ubot(int(oldowner))
                await asyncio.sleep(1)
                for mod in PLUGINS:
                    importlib.reload(importlib.import_module(f"plugins.{mod}"))
                for chat in WAJIB_JOIN:
                    try:
                        await kn_client.join_chat(chat)
                    except Exception:
                        pass
                prefix = alice.get_prefix(kn_client.me.id)
                keyb = ButtonUtils.start_menu(is_admin=False)
                exp = await dB.get_expired_date(kn_client.me.id)
                expir = exp.astimezone(timezone("Asia/Jakarta")).strftime(
                    "%Y-%m-%d %H:%M"
                )
                text_done = f"""
<blockquote><b>🔥 {bot.me.mention} Berhasil Di Aktifkan
➡️ Akun: <a href=tg://openmessage?user_id={kn_client.me.id}>{kn_client.me.first_name} {kn_client.me.last_name or ''}</a>
➡️ ID: <code>{kn_client.me.id}</code>
➡️ Prefixes: {''.join(prefix)}
➡️ Masa Aktif: {expir}</b></blockquote>

<blockquote><b>{new_ref}</b></blockquote>"""
                await bot_msg.edit(
                    text_done, disable_web_page_preview=True, reply_markup=keyb
                )
                return await client.send_message(
                    LOG_SELLER,
                    f"""
<b>❏ Notifikasi Claim Token</b>
<b> ├ Akun :</b> <a href=tg://user?id={kn_client.me.id}>{kn_client.me.first_name} {kn_client.me.last_name or ''}</a> 
<b> ╰ ID :</b> <code>{kn_client.me.id}</code>
""",
                    reply_markup=ikb(
                        [
                            [
                                (
                                    "Cek Kadaluarsa",
                                    f"cek_masa_aktif {kn_client.me.id}",
                                    "callback_data",
                                )
                            ]
                        ]
                    ),
                    disable_web_page_preview=True,
                )
            except Exception as er:
                logger.error(f"ERROR CLAIM TOKEN: {traceback.format_exc()}")
    elif data == "revoke_token":
        buttons = ikb([[("❌ Tutup", "buttonclose")]])
        if user_id not in alice._get_my_id:
            return await query.edit_message_text(
                "<b>Maaf, kamu bukan pengguna userbot ini dan kamu tidak memiliki token.</b>",
                reply_markup=buttons,
            )
        _, txt = await tokenref.revoke_token(str(user_id))
        return await query.edit_message_text(txt, reply_markup=buttons)
