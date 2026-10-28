import asyncio
from datetime import datetime, timedelta

from pyrogram import raw
from pyrogram.errors import (ChannelInvalid, FloodWait, InputUserDeactivated,
                             PeerIdInvalid, UserIsBlocked, UsernameNotOccupied)
from pyrogram.helpers import kb
from pytz import timezone

from clients import bot, alice
from config import AKSES_DEPLOY, BOT_ID, LOG_SELLER, SUDO_OWNERS
from database import dB, state

from .addubot_command import setExpiredUser


async def set_plan(client, message):
    user = message.from_user.id
    reseller = await dB.get_list_from_var(BOT_ID, "SELLER")
    if user not in reseller:
        return await message.reply("<b>Kamu bukan reseller!!</b>")
    user_id, plan = await client.extract_user_and_reason(message)
    if not user_id:
        return await message.reply(
            f"{message.text.split()[0]} user_id/username plan\nContoh: {message.text.split()[0]} @username is_pro"
        )
    try:
        get_id = (await client.get_users(user_id)).id
    except Exception as error:
        return await message.reply(str(error))
    bef_plan = await dB.get_var(user_id, "plan")
    if not plan:
        return await message.reply("Silahkan berikan plan `basic` atau `is_pro`")
    await dB.set_var(user_id, "plan", plan)
    return await message.reply(
        f"Pengguna {get_id} telah ditetapkan plan dari: `{bef_plan}` menjadi `{plan}` ."
    )


async def add_pro_user(client, message):
    user = message.from_user
    reseller = await dB.get_list_from_var(BOT_ID, "SELLER")
    if user.id not in reseller:
        return await message.reply("<b>Kamu bukan reseller!!</b>")
    user_id, get_bulan = await client.extract_user_and_reason(message)
    if not user_id:
        return await message.reply(
            f"<b>{message.text.split()[0]} [user_id/username - bulan]</b>"
        )
    try:
        get_id = (await client.get_users(user_id)).id
    except Exception as error:
        return await message.reply(str(error))
    if not get_bulan:
        get_bulan = 1
    premium = AKSES_DEPLOY
    if get_id in premium:
        return await message.reply(
            f"Pengguna denga ID : `{get_id}` sudah memiliki akses !"
        )
    AKSES_DEPLOY.append(get_id)
    if not await dB.get_expired_date(get_id):
        await setExpiredUser(get_id)
    await message.reply(
        f"✅  <b>Akses diberikan kepada {get_id}!! Silahkan pergi ke @{bot.me.username}"
    )
    target1 = f"<a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or ''}</a>"
    try:
        target = await bot.get_users(user_id)
        target2 = f"<a href=tg://user?id={target.id}>{target.first_name} {target.last_name or ''}</a>"
    except Exception:
        target2 = get_id
    await bot.send_message(
        LOG_SELLER, f"<b>User: {target1} gives access to: {target2}, plan pro</b>"
    )
    if message.from_user.id not in SUDO_OWNERS:
        state.set(get_id, "seller", message.from_user.id)
    await dB.set_var(get_id, "plan", "is_pro")
    try:
        return await bot.send_message(
            get_id,
            f"Selamat ! Akun anda sudah memiliki akses untuk pembuatan Userbot",
            reply_markup=kb(
                [["✅ Lanjutkan Buat Userbot"]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
    except Exception:
        pass


async def add_prem_user(client, message):
    user = message.from_user
    reseller = await dB.get_list_from_var(BOT_ID, "SELLER")
    if user.id not in reseller:
        return await message.reply("<b>Kamu bukan reseller!!</b>")
    user_id, get_bulan = await client.extract_user_and_reason(message)
    if not user_id:
        return await message.reply(
            f"<b>{message.text.split()[0]} [user_id/username - bulan]</b>"
        )
    try:
        get_id = (await client.get_users(user_id)).id
    except Exception as error:
        return await message.reply(str(error))
    if not get_bulan:
        get_bulan = 1
    premium = AKSES_DEPLOY
    if get_id in premium:
        return await message.reply(
            f"Pengguna denga ID : `{get_id}` sudah memiliki akses !"
        )
    AKSES_DEPLOY.append(get_id)
    if not await dB.get_expired_date(get_id):
        await setExpiredUser(get_id)
    await message.reply(
        f"✅  <b>Akses diberikan kepada {get_id}!! Silahkan pergi ke @{bot.me.username}"
    )
    target1 = f"<a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or ''}</a>"
    try:
        target = await bot.get_users(user_id)
        target2 = f"<a href=tg://user?id={target.id}>{target.first_name} {target.last_name or ''}</a>"
    except Exception:
        target2 = get_id
    await bot.send_message(
        LOG_SELLER, f"<b>User: {target1} gives access to: {target2}, plan basic</b>"
    )
    if message.from_user.id not in SUDO_OWNERS:
        state.set(get_id, "seller", message.from_user.id)
    await dB.set_var(get_id, "plan", "basic")
    try:
        return await bot.send_message(
            get_id,
            f"Selamat ! Akun anda sudah memiliki akses untuk pembuatan Userbot",
            reply_markup=kb(
                [["✅ Lanjutkan Buat Userbot"]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
    except Exception:
        pass


async def un_prem_user(client, message):
    user = message.from_user
    reseller = await dB.get_list_from_var(BOT_ID, "SELLER")
    if user.id not in reseller:
        return await message.reply("<b>Kamu bukan reseller!!</b>")
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply("Balas pesan pengguna atau berikan user_id/username")
    try:
        user = await client.get_users(user_id)
    except Exception as error:
        await message.reply(str(error))
    delpremium = AKSES_DEPLOY
    if user.id not in delpremium:
        return await message.reply("Tidak ditemukan")
    AKSES_DEPLOY.remove(user.id)
    return await message.reply(f" ✅ {user.mention} berhasil dihapus")


async def add_seller(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    user = None
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply("Balas pesan pengguna atau berikan user_id/username")
    try:
        user = await client.get_users(user_id)
    except Exception as error:
        await message.reply(str(error))
    seles = await dB.get_list_from_var(BOT_ID, "SELLER")
    if user.id in seles:
        return await message.reply("Sudah menjadi reseller.")

    await dB.add_to_var(BOT_ID, "SELLER", user.id)
    return await message.reply(f"✅ {user.mention} telah menjadi reseller")


async def un_seller(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    user = None
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply("Balas pesan pengguna atau berikan user_id/username")
    try:
        user = await client.get_users(user_id)
    except Exception as error:
        await message.reply(str(error))
    seles = await dB.get_list_from_var(BOT_ID, "SELLER")
    if user.id not in seles:
        return await message.reply("Tidak ditemukan")
    await dB.remove_from_var(BOT_ID, "SELLER", user.id)
    return await message.reply(f"{user.mention} berhasil dihapus")


async def send_broadcast(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    users = await dB.get_list_from_var(client.me.id, "BROADCAST")
    if not message.reply_to_message:
        return await message.reply("<b>Silahkan balas ke pesan!</b>")
    reply = message.reply_to_message
    gagal = 0
    sukses = 0
    for i in users:
        try:
            await reply.copy(i)
            sukses += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await reply.copy(i)
            sukses += 1
        except UserIsBlocked:
            await dB.remove_from_var(BOT_ID, "BROADCAST", i)
            gagal += 1
            continue
        except PeerIdInvalid:
            await dB.remove_from_var(BOT_ID, "BROADCAST", i)
            gagal += 1
            continue
        except InputUserDeactivated:
            await dB.remove_from_var(BOT_ID, "BROADCAST", i)
            gagal += 1
            continue
    return await message.reply(
        f"<b>Berhasil mengirim pesan ke `{sukses}` pengguna, gagal ke `{gagal}` pengguna, dari `{len(users)}` pengguna.</b>",
    )


async def mass_report(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    if len(message.command) < 2:
        await message.reply(
            "Channel atau Grup .\nUsage: `massreport [user|channel] username`"
        )
        return
    command, uname = client.extract_type_and_msg(message)
    if command == "channel":
        report_text = (
            "Saluran ini menyebarkan berita palsu, menyesatkan masyarakat, sehingga memicu agresi "
            "dan mengajak berperang antarnegara. Saluran ini memuat unggahan yang mengandung ancaman "
            "kekerasan terhadap nyawa dan kesehatan warga Ukraina. Berdasarkan hukum internasional, "
            "hal ini dianggap sebagai terorisme. Oleh karena itu, kami memohon kepada Anda untuk "
            "memblokirnya sesegera mungkin!"
        )
        status_msg = await message.reply(f"⏳ Report @{uname}...")
        try:
            for user in alice._ubot:
                try:
                    peer = await user.resolve_peer(f"@{uname}")
                except UsernameNotOccupied:
                    await message.reply(f"❌ Username @{uname} tidak ada.")
                    return
                except ChannelInvalid:
                    await message.reply(
                        f"❌ Channel @{uname} is invalid or not accessible."
                    )
                    return
                except PeerIdInvalid:
                    await message.reply(f"❌ Cannot find entity @{uname}.")
                    return
                await user.invoke(
                    raw.functions.account.ReportPeer(
                        peer=peer,
                        reason=raw.types.InputReportReasonOther(),
                        message=report_text,
                    )
                )

            return await status_msg.edit(f"✅ @{uname} Berhasil di report!!.")

        except Exception as e:
            import traceback

            error_traceback = traceback.format_exc()
            return await status_msg.reply(
                f"❌ Error occurred while reporting:\n`{error_traceback}`"
            )
    elif command == "user":
        try:
            status_msg = await message.reply(
                f"⏳ Processing report for user @{uname}..."
            )
            report_text = (
            "Saluran ini menyebarkan berita palsu, menyesatkan masyarakat, sehingga memicu agresi "
            "dan mengajak berperang antarnegara. Saluran ini memuat unggahan yang mengandung ancaman "
            "kekerasan terhadap nyawa dan kesehatan warga Ukraina. Berdasarkan hukum internasional, "
            "hal ini dianggap sebagai terorisme. Oleh karena itu, kami memohon kepada Anda untuk "
            "memblokirnya sesegera mungkin!"
            )
            for user in alice._ubot:
                try:
                    peer = await user.resolve_peer(f"@{uname}")
                except UsernameNotOccupied:
                    await status_msg.edit(f"❌ Username @{uname} does not exist.")
                    return
                except PeerIdInvalid:
                    await status_msg.edit(f"❌ Cannot find user @{uname}.")
                    return
                await user.invoke(
                    raw.functions.account.ReportPeer(
                        peer=peer,
                        reason=raw.types.InputReportReasonOther(),
                        message=report_text,
                    )
                )
            return await status_msg.edit(
                f"✅ User @{uname} has been reported successfully."
            )

        except Exception as e:
            import traceback

            error_traceback = traceback.format_exc()
            return await status_msg.edit(
                f"❌ Error occurred while reporting user:\n`{error_traceback}`"
            )


async def get_seles_user(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    text = ""
    count = 0
    seles = await dB.get_list_from_var(BOT_ID, "SELLER")
    for user_id in seles:
        try:
            user = await client.get_users(user_id)
            count += 1
            userlist = f"• {count}: <a href=tg://user?id={user.id}>{user.first_name} {user.last_name or ''}</a> > <code>{user.id}</code>"
        except Exception:
            continue
        text += f"{userlist}\n"
    if not text:
        return await message.reply_text("Tidak ada pengguna yang ditemukan")
    else:
        return await message.reply_text(text)


async def addexpired_user(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    user_id, get_day = await client.extract_user_and_reason(message)
    if not user_id:
        return await message.reply(f"{message.text.split()[0]} user_id/username - hari")
    try:
        get_id = (await client.get_users(user_id)).id
    except Exception as error:
        return await message.reply(str(error))
    if not get_day:
        get_day = 30
    now = datetime.now(timezone("Asia/Jakarta"))
    expire_date = now + timedelta(days=int(get_day))
    await dB.set_expired_date(user_id, expire_date)
    return await message.reply(f"{get_id} telah diaktifkan selama {get_day} hari.")


async def cek_expired(client, message):
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply("Pengguna tidak ditemukan")
    expired_date = await dB.get_expired_date(user_id)
    if not expired_date:
        return await message.reply(f"{user_id} belum diaktifkan.")
    expir = expired_date.astimezone(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M")
    return await message.reply(f"{user_id} aktif hingga {expir}.")


async def unexpired(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    user = None
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply("User tidak ditemukan")
    try:
        user = await client.get_users(user_id)
    except Exception as error:
        return await message.reply(str(error))
    await dB.rem_expired_date(user.id)
    return await message.reply(f"✅ {user.id} expired telah dihapus")


async def get_prem_user(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in SUDO_OWNERS:
        return
    text = ""
    count = 0
    for user_id in AKSES_DEPLOY:
        try:
            user = await client.get_users(user_id)
            count += 1
            userlist = f"• {count}: <a href=tg://user?id={user.id}>{user.first_name} {user.last_name or ''}</a> > <code>{user.id}</code>"
        except Exception:
            continue
        text += f"{userlist}\n"
    if not text:
        return await message.reply_text("Tidak ada pengguna yang ditemukan")
    else:
        return await message.reply_text(text)


async def seller_cmd(client, message):
    reseller = await dB.get_list_from_var(BOT_ID, "SELLER")
    if not reseller:
        return await message.reply("<b>Kamu belum memiliki reseller!!</b>")
    msg = ""
    for count, usr in enumerate(reseller, 1):
        try:
            data = await dB.get_var(usr, "penjualan") or 0
            mention = (await bot.get_users(int(usr))).mention
        except Exception:
            continue
        msg += f"{count}.<b>{mention} | penjualan bulan ini</b> {data}\n"
    return await message.reply(msg)
