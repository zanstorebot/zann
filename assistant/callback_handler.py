import traceback

from command import (ask_callback, apkinfocb, basic_plugins, batal_pesan, bola_date,
                     bola_matches, callback_alert, callback_cerpen,
                     cancel_payment, cb_help, cb_markdown, cb_notes,
                     cb_trial, cek_expired_cb, cek_status_akun, chat_gpt,
                     chose_plan, cine_plax, closed_bot, closed_user,
                     confirm_pay, contact_admins, copy_msg, cq_tiktok,
                     del_userbot, dl_spot, dln_youtube, gen_pro, get_bio,
                     get_font, gpt_voice, jawab_pesan, kasih_ubot,
                     kurang_tambah, mari_buat_userbot, news_, next_font,
                     next_textpro, nxpin_search, nxt_spotify, nxt_tsearch,
                     pm_warn, prev_font, prev_textpro, prevnext_userbot,
                     prevnext_userbot2, pro_plugins, profil_user,
                     referal_command, refresh_cat, reset_costum_text,
                     reset_emoji, reset_prefix, rest_anime, rest_comic,
                     rest_donghua, restart_userbot, select_model,
                     sosmed_callback, start_home, token_cmd, tools_referral,
                     tools_token, tools_userbot, update_kode, use_referral,
                     user_aggre, viewchord, viewlyric, addgroup_bot, play_btn_callback)
from config import SUDO_OWNERS
from helpers import CMD, trigger
from logs import logger

MESSAGE_DICT = {}
CONVERSATIONS = {}


@CMD.REGEX(trigger)
async def _(client, message):
    try:
        text = message.text

        if text in [
            "Mulai Buat Userbot",
            "✨ Pembuatan Ulang Userbot",
            "✅ Lanjutkan Buat Userbot",
        ]:
            return await mari_buat_userbot(client, message)
        elif text == "❓ Status Akun":
            return await cek_status_akun(client, message)
        elif text.startswith("🔄 Reset"):
            data = text.split(" ")[2]
            if data == "Emoji":
                return await reset_emoji(client, message)
            elif data == "Prefix":
                return await reset_prefix(client, message)
            elif data == "Text":
                return await reset_costum_text(client, message)
        elif text == "Trial Userbot":
            return await cb_trial(client, message)
        elif text == "Restart Userbot":
            return await restart_userbot(client, message)
        elif text == "Updates":
            return await update_kode(client, message)
        elif text == "Plan Basic":
            return await basic_plugins(client, message)
        elif text == "Cek Fitur":
            return await pro_plugins(client, message)
        elif text == "Hubungi Admins":
            return await contact_admins(client, message)
        elif text == "↩️ Beranda":
            return await start_home(client, message)
        elif text == "Referral":
            return await referal_command(client, message)
        elif text == "Token":
            return await token_cmd(client, message)

        # TAMBAHKAN INI PALING BAWAH
        if await ask_dispatch(client, message):
            return

    except Exception as er:
        logger.error(f"Terjadi error: {str(er)}")


@CMD.CALLBACK()
async def _(client, callback):
    try:
        query = callback.data
        logger.info(f"Name callback query: {query}")
        if query == "buttonclose":
            return await closed_bot(client, callback)

        # tombol bubble di pesan /start (rich message)
        elif query.startswith("btn_"):
            logger.info(f"btn callback: {query}")
            fn = {
                "btn_mulai": mari_buat_userbot,
                "btn_trial": cb_trial,
                "btn_fitur": pro_plugins,
                "btn_referral": referal_command,
                "btn_token": token_cmd,
                "btn_resetprefix": reset_prefix,
                "btn_addgroup": addgroup_bot,
                "btn_updates": update_kode,
            }.get(query)
            logger.info(f"btn fn: {fn}")
            if query == "btn_updates" and callback.from_user.id not in SUDO_OWNERS:
                return await callback.answer("Khusus owner", show_alert=True)
            if not fn:
                return await callback.answer("Tombol tidak dikenal", show_alert=True)
            msg = callback.message
            msg.from_user = callback.from_user  # fungsi message-trigger butuh user asli
            await callback.answer()
            try:
                return await fn(client, msg)
            except Exception:
                logger.error(f"btn fn error: {traceback.format_exc()}")
                return await callback.answer("Terjadi error, coba lagi.", show_alert=True)

        # sesi hubungi admin / balas pesan
        elif query.startswith("pl_"):
            return await play_btn_callback(client, callback)
        elif query.startswith("jawab_pesan"):
            return await jawab_pesan(client, callback)
        elif query.startswith("batal "):
            return await batal_pesan(client, callback)
        elif query.startswith("profil"):
            return await profil_user(client, callback)

        elif query.startswith("close"):
            return await closed_user(client, callback)
        elif query.startswith("askbot_"):
             return await ask_callback(client, callback)
        elif query.startswith("pm_warn"):
            return await pm_warn(client, callback)
        elif query.startswith("getbio_"):
            return await get_bio(client, callback)
        elif query.startswith("copymsg_"):
            return await copy_msg(client, callback)
        elif query.startswith("cb_"):
            return await cb_notes(client, callback)
        elif query.startswith("get_font"):
            return await get_font(client, callback)
        elif query.startswith("prev_font"):
            return await prev_font(client, callback)
        elif query.startswith("next_font"):
            return await next_font(client, callback)
        elif query.startswith("refresh_cat"):
            return await refresh_cat(client, callback)
        elif query.startswith("prev_textpro"):
            return await prev_textpro(client, callback)
        elif query.startswith("next_textpro"):
            return await next_textpro(client, callback)
        elif query.startswith("genpro"):
            return await gen_pro(client, callback)
        elif query.startswith("nxttsearch"):
            return await nxt_tsearch(client, callback)
        elif query.startswith("cqtiktok"):
            return await cq_tiktok(client, callback)
        elif query.startswith("nxtspotify"):
            return await nxt_spotify(client, callback)
        elif query.startswith("dlspot"):
            return await dl_spot(client, callback)
        elif query.startswith("nxpinsearch"):
            return await nxpin_search(client, callback)
        elif query.startswith("bola_date"):
            return await bola_date(client, callback)
        elif query.startswith("bola_matches"):
            return await bola_matches(client, callback)
        elif query.startswith("restanime_"):
            return await rest_anime(client, callback)
        elif query.startswith("restdonghua_"):
            return await rest_donghua(client, callback)
        elif query.startswith("restcomic_"):
            return await rest_comic(client, callback)
        elif query.startswith("news_"):
            return await news_(client, callback)
        elif query.startswith("selectmodel_"):
            return await select_model(client, callback)
        elif query.startswith("chatgpt_"):
            return await chat_gpt(client, callback)
        elif query.startswith("gptvoice_"):
            return await gpt_voice(client, callback)
        elif query.startswith("cineplax"):
            return await cine_plax(client, callback)

        elif query == "go_payment":
            return await user_aggre(client, callback)
        elif query == "ubot":
            return await kasih_ubot(client, callback)
        elif query.startswith("kurang") or query.startswith("tambah"):
            return await kurang_tambah(client, callback)
        elif query.startswith("confirm"):
            return await confirm_pay(client, callback)
        elif query == "batal_payment":
            return await cancel_payment(client, callback)

        elif query.startswith("del_ubot"):
            return await del_userbot(client, callback)
        elif query.startswith("prev_ub") or query.startswith("next_ub"):
            return await prevnext_userbot(client, callback)
        elif query.startswith("fakeprev_ub") or query.startswith("fakenext_ub"):
            return await prevnext_userbot2(client, callback)
        elif (
            query.startswith("get_otp")
            or query.startswith("get_phone")
            or query.startswith("get_faktor")
            or query.startswith("ub_deak")
            or query.startswith("deak_akun")
        ):
            return await tools_userbot(client, callback)

        elif query.startswith("claim_referral") or query.startswith("status_referral"):
            return await tools_referral(client, callback)
        elif query.startswith("use_expired") or query.startswith("use_userbot"):
            return await use_referral(client, callback)
        elif query.startswith("use_token") or query.startswith("revoke_token"):
            return await tools_token(client, callback)

        elif query.startswith("markdown"):
            return await cb_markdown(client, callback)
        elif query.startswith("help_"):
            return await cb_help(client, callback)
        elif query.startswith("cerpennext_"):
            return await callback_cerpen(client, callback)
        elif query.startswith("cek_masa_aktif"):
            return await cek_expired_cb(client, callback)
        elif query.startswith("dlnyt_"):
            return await dln_youtube(client, callback)
        elif query.startswith("sosmedcb_"):
            return await sosmed_callback(client, callback)
        elif query.startswith("viewchord_"):
            return await viewchord(client, callback)
        elif query.startswith("viewlyric_"):
            return await viewlyric(client, callback)
        elif query.startswith("planusers"):
            return await chose_plan(client, callback)
        elif query.startswith("alertcb_"):
            return await callback_alert(client, callback)
        elif query.startswith("apkinfocb_"):
            return await apkinfocb(client, callback)
    except Exception:
        logger.error(f"Callback error: {traceback.format_exc()}")
