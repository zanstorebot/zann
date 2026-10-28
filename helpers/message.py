from typing import Optional

from pytz import timezone

from clients import alice
from config import BOT_ID, BOT_NAME, USENAME_OWNER
from database import dB

from .auto_referal import TokenReferal


class Message:
    """Enhanced message templates with modern formatting"""

    JAKARTA_TZ = timezone("Asia/Jakarta")

    # HTML formatting templates
    USER_MENTION = "<a href=tg://user?id={id}>{name}</a>"
    CODE_BLOCK = "<code>{text}</code>"
    SECTION_START = "<b>❏ {title}</b>"
    SECTION_ITEM = "<b>├ {label}:</b> {value}"
    SECTION_END = "<b>╰ {label}</b> {value}"

    @staticmethod
    def ReplyCheck(message):
        reply_id = None
        if message.reply_to_message:
            reply_id = message.reply_to_message.id
        elif not message.from_user:
            reply_id = message.id
        return reply_id

    @staticmethod
    async def _ads() -> str:
        txt = await dB.get_var(BOT_ID, "ads")
        if txt:
            msg = txt
        else:
            msg = f"Masih kosong, jika ingin promosi ads hubungi {USENAME_OWNER}"
        return msg

    @classmethod
    def _format_user_mention(
        cls, user_id: int, first_name: str, last_name: Optional[str] = None
    ) -> str:
        """Format user mention with full name"""
        full_name = f"{first_name} {last_name or ''}".strip()
        return cls.USER_MENTION.format(id=user_id, name=full_name)

    @classmethod
    def expired_message(cls, client) -> str:
        """Generate expired account notification"""
        return f"""
{cls.SECTION_START.format(title="Notifikasi")}
{cls.SECTION_ITEM.format(
    label="Akun",
    value=cls._format_user_mention(client.me.id, client.me.first_name, client.me.last_name)
)}
{cls.SECTION_ITEM.format(label="ID", value=cls.CODE_BLOCK.format(text=client.me.id))}
{cls.SECTION_END.format(label="Status", value="Masa Aktif Telah Habis")}
"""

    @classmethod
    async def welcome_message(cls, client, message) -> str:
        """Generate personalized welcome message"""
        tokenref = await TokenReferal.create()
        if str(message.from_user.id) not in tokenref.users:
            Referral = await tokenref.generate_referral_code(str(message.from_user.id))
        else:
            getref = tokenref.users[str(message.from_user.id)]
            Referral = getref.get("referral_code")
        return f"""
<b>✨ Selamat datang, {cls._format_user_mention(
    message.from_user.id,
    message.from_user.first_name,
    message.from_user.last_name
)}!</b>

<b>🤖 Saya adalah <u>[{BOT_NAME}](https://t.me/{client.me.username})</u>, asisten pintar yang akan membantu Anda membuat userbot dengan mudah dan cepat.</b></blockquote>

<blockquote><b>Kode Referral Kamu: <code>{Referral}</code>\nAjak 2 teman kamu untuk membeli userbot dengan kode referral kamu, dan kamu mendapatkan masa aktif gratis 1 bulan.</b></blockquote>
<i>klik emoji api untuk animasi</i> ->
"""

    @staticmethod
    async def userbot(count):
        expired_date = await dB.get_expired_date(alice._ubot[int(count)].me.id)
        expir = expired_date.astimezone(timezone("Asia/Jakarta")).strftime(
            "%Y-%m-%d %H:%M"
        )
        return f"""
<b>❏ Userbot ke </b> <code>{int(count) + 1}/{len(alice._ubot)}</code>
<b> ├ Akun:</b> <a href=tg://user?id={alice._ubot[int(count)].me.id}>{alice._ubot[int(count)].me.first_name} {alice._ubot[int(count)].me.last_name or ''}</a> 
<b> ├ ID:</b> <code>{alice._ubot[int(count)].me.id}</code>
<b> ╰ Expired</b> <code>{expir}</code>
"""

    @staticmethod
    def deak(X):
        return f"""
<b>Attention !!</b>
<b>Akun:</b> <a href=tg://user?id={X.me.id}>{X.me.first_name} {X.me.last_name or ''}</a>
<b>ID:</b> <code>{X.me.id}</code>
<b>Reason:</b> <code>ᴅɪ ʜᴀᴘᴜs ᴅᴀʀɪ ᴛᴇʟᴇɢʀᴀᴍ</code>
"""

    @staticmethod
    async def policy_message() -> str:
        """Generate enhanced policy and terms message"""
        return f"""<b>🤖 {BOT_NAME} Metode pembayaran 
Kami menggunakan QRIS otomatis
jika QRIS tidak merespon silahkan hubungi owner.</b>
"""

    @staticmethod
    def format_rupiah(angka):
        return f"Rp{angka:,}".replace(",", ".")

    @staticmethod
    def TEXT_PAYMENT(harga, total, bulan, plan, diskon=0):
        return f"""
<blockquote><b>Sebelum melanjutkan pembayaran silahkan pilih durasi terlebih dahulu.

Harga per bulan: <code>{Message.format_rupiah(harga)}</code>
📅 Masa aktif: <code>{bulan} bulan</code>
🎮 Plan: <code>{plan}</code>
🖨️ Total yang harus dibayar: <code>{Message.format_rupiah(total)}</code>
</b></blockquote>
"""

    @staticmethod
    def chosePlan():
        return """
**🧩 Plan Basic**
    <blockquote>Nikmati akses ke 38 fitur unggulan yang cukup untuk kebutuhan standar.
    Cek semua fiturnya di tombol 🧩 Plan Basic.
    Fitur bisa bertambah atau berkurang sesuai pengembangan dari developer.</blockquote>

**💎 Plan Pro**
    <blockquote>Unlock semua kemampuan dengan 90 fitur premium yang super lengkap!
    Lihat daftar fitur lengkapnya di tombol 💎 Plan Pro.
    Fitur akan terus dikembangkan dan bisa berubah sesuai keputusan developer.</blockquote>

**Silahkan pilih plan sebelum melakukan pembayaran!!**"""
