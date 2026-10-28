import asyncio
import time
import traceback
from collections import defaultdict
from html import escape

from clients import bot
from database import dB, state

from .buttons import ButtonUtils
from .emoji_logs import Emoji
from .message import Message
from .tools import Tools

GODZILA = 5406757183008291910
WORK = 5107153978269893301
PLANET = 4961155507164283482
PERI = 5089416218603946547
PENING = 5089613774214660825
LOVE = 5355055934362107020
BELAJAR = 5107633812016202563
FUCK = 4961092903720977544
HMM = 5188230385154149088

AFK_EFFECTS = {
    "godzila": GODZILA,
    "work": WORK,
    "planet": PLANET,
    "peri": PERI,
    "pening": PENING,
    "love": LOVE,
    "fuck": FUCK,
    "belajar": BELAJAR,
    "hmm": HMM,
}

# Lama pesan AFK sebelum dihapus otomatis (detik)
AFK_DELETE_DELAY = 30

afk_spam_tracker = defaultdict(list)


def _entity_tags(e):
    name = e.type.name
    simple = {
        "BOLD": ("<b>", "</b>"),
        "ITALIC": ("<i>", "</i>"),
        "UNDERLINE": ("<u>", "</u>"),
        "STRIKETHROUGH": ("<s>", "</s>"),
        "SPOILER": ("<spoiler>", "</spoiler>"),
        "CODE": ("<code>", "</code>"),
        "BLOCKQUOTE": ("<blockquote>", "</blockquote>"),
        "EXPANDABLE_BLOCKQUOTE": ("<blockquote expandable>", "</blockquote>"),
    }
    if name in simple:
        return simple[name]
    if name == "PRE":
        lang = getattr(e, "language", None)
        open_tag = f'<pre language="{lang}">' if lang else "<pre>"
        return open_tag, "</pre>"
    if name == "TEXT_LINK" and e.url:
        return f'<a href="{escape(e.url)}">', "</a>"
    if name == "TEXT_MENTION" and e.user:
        return f'<a href="tg://user?id={e.user.id}">', "</a>"
    if name == "CUSTOM_EMOJI" and e.custom_emoji_id:
        return f'<emoji id="{e.custom_emoji_id}">', "</emoji>"
    return None


def entities_to_html(text, entities, start=0):
    """Ubah text + entities Telegram jadi HTML.
    start = index karakter awal teks AFK (setelah command dibuang).
    Offset entity Telegram memakai UTF-16, jadi dihitung per code unit."""
    raw = text.encode("utf-16-le")
    units = [raw[i : i + 2] for i in range(0, len(raw), 2)]
    start_u = len(text[:start].encode("utf-16-le")) // 2
    total = len(units) - start_u
    opens, closes = {}, {}
    for e in entities or []:
        tags = _entity_tags(e)
        if not tags:
            continue
        s = max(e.offset - start_u, 0)
        en = min(e.offset + e.length - start_u, total)
        if en <= s:
            continue
        opens.setdefault(s, []).append((-(en - s), tags[0]))
        closes.setdefault(en, []).append((s, tags[1]))
    out, run = [], bytearray()

    def flush():
        if run:
            out.append(escape(bytes(run).decode("utf-16-le", "ignore"), quote=False))
            run.clear()

    for pos in range(total + 1):
        if pos in closes or pos in opens:
            flush()
            for _, tag in sorted(closes.get(pos, []), key=lambda x: -x[0]):
                out.append(tag)
            for _, tag in sorted(opens.get(pos, []), key=lambda x: x[0]):
                out.append(tag)
        if pos < total:
            run.extend(units[start_u + pos])
    flush()
    return "".join(out)


class AFK_:
    @staticmethod
    async def set_afk(client, message):
        emo = Emoji(client)
        await emo.get()
        try:
            parts = message.text.split(maxsplit=2)
            if len(parts) < 2:
                return await message.reply(
                    f"{emo.gagal}<b>Contoh:</b> <code>afk [code_effect] sedang tidur</code>"
                )
            effect_name = None
            effect_id = None
            possible_effect = parts[1].lower()
            if possible_effect in AFK_EFFECTS:
                effect_name = possible_effect
                effect_id = AFK_EFFECTS[possible_effect]
                afk_raw = parts[2] if len(parts) > 2 else None
            else:
                afk_raw = message.text.split(maxsplit=1)[1]
            if afk_raw:
                afk_text = entities_to_html(
                    message.text,
                    message.entities,
                    len(message.text) - len(afk_raw),
                )
            else:
                afk_text = "Sedang AFK."
            value = {
                "type": "text",
                "file_id": "",
                "result": {
                    "text": afk_text,  # berisi HTML (format ikut tersimpan)
                    "entities": [],
                },
                "effect_id": effect_id,
                "effect_name": effect_name,
            }
            await dB.set_var(client.me.id, "AFK", value)
            effect_status = (
                f"\n<b>Effect:</b> <code>{effect_name}</code>" if effect_name else ""
            )
            return await message.reply(
                f"{emo.sukses}<b>AFK berhasil diaktifkan.</b>\n"
                f"<b>Pesan:</b>\n{afk_text}"
                f"{effect_status}"
            )
        except Exception as er:
            return await message.reply(
                f"{emo.gagal}<b>ERROR:</b> <code>{str(er)}</code>"
            )

    @staticmethod
    async def list_efek(client, message):
        emo = Emoji(client)
        await emo.get()
        if not AFK_EFFECTS:
            return await message.reply(
                f"{emo.gagal}<b>Belum ada efek yang tersedia.</b>"
            )
        daftar = "\n".join(f"• <code>{name}</code>" for name in AFK_EFFECTS)
        return await message.reply(
            f"{emo.sukses} <b>Daftar efek AFK ({len(AFK_EFFECTS)}):</b>\n\n"
            f"<blockquote>{daftar}\n\n</blockquote>"
            f"<b>Contoh:</b> <code>afk [nama_efek] sedang tidur</code>"
        )

    @staticmethod
    async def _auto_delete(msg, delay=AFK_DELETE_DELAY):
        """Hapus pesan setelah `delay` detik."""
        try:
            await asyncio.sleep(delay)
            await msg.delete()
        except Exception:
            pass

    @staticmethod
    async def get_afk(client, message):
        """Kirim balasan AFK, lalu hapus otomatis setelah AFK_DELETE_DELAY detik."""
        sent = await AFK_._get_afk(client, message)
        if sent is not None and hasattr(sent, "delete"):
            # create_task supaya handler tidak tertahan selama delay
            asyncio.create_task(AFK_._auto_delete(sent, AFK_DELETE_DELAY))
        return sent

    @staticmethod
    async def _get_afk(client, message):
        # Reply AFK hanya untuk chat private, grup/channel diabaikan
        if message.chat.type.name != "PRIVATE":
            return
        emo = Emoji(client)
        await emo.get()
        try:
            data = await dB.get_var(client.me.id, "AFK")
            if not data:
                return
            if not message.from_user:
                return
            async for last_message in client.get_chat_history(
                message.chat.id, limit=1
            ):
                if last_message.reply_markup:
                    try:
                        await last_message.delete()
                    except Exception:
                        pass
            ignored = await dB.get_list_from_var(client.me.id, "IGNORE")
            if message.from_user.id in ignored:
                return
            uid = message.from_user.id
            now = time.time()
            afk_spam_tracker[uid] = [t for t in afk_spam_tracker[uid] if now - t < 10]
            afk_spam_tracker[uid].append(now)
            if len(afk_spam_tracker[uid]) >= 5:
                await dB.add_to_var(client.me.id, "IGNORE", uid)
                return
            afk_type = data.get("type", "text")
            file_id = data.get("file_id", "")
            result = data.get("result", {})
            effect_id = data.get("effect_id")
            main_text = result.get("text", "")
            entities_data = result.get("entities", [])
            entities = [Tools.convert_entity(entity) for entity in entities_data]
            reply_kwargs = {"reply_to_message_id": message.id}
            if effect_id:
                reply_kwargs["effect_id"] = effect_id
            one, button = ButtonUtils.parse_msg_buttons(main_text)
            # AFK dengan inline button:
            # Effect tidak dapat dipasang ke hasil inline secara langsung.
            if button:
                state.set(client.me.id, "afk", id(message))
                try:
                    return await ButtonUtils.send_inline_bot_result(
                        message,
                        message.chat.id,
                        bot.me.username,
                        "inline_afk",
                        reply_to_message_id=Message.ReplyCheck(message),
                    )
                except Exception:
                    if afk_type == "text":
                        return await message.reply(
                            one,
                            entities=entities,
                            **reply_kwargs,
                        )
                    return await AFK_._send_media_afk(
                        client=client,
                        message=message,
                        media_type=afk_type,
                        file_id=file_id,
                        caption=one,
                        entities=entities,
                        effect_id=effect_id,
                    )
            # AFK teks tanpa tombol
            if afk_type == "text":
                return await message.reply(
                    main_text,
                    entities=entities,
                    **reply_kwargs,
                )
            # AFK media tanpa tombol
            return await AFK_._send_media_afk(
                client=client,
                message=message,
                media_type=afk_type,
                file_id=file_id,
                caption=main_text,
                entities=entities,
                effect_id=effect_id,
            )
        except Exception:
            logger_error = traceback.format_exc()
            try:
                return await message.reply(
                    f"<b>AFK Error:</b><code>{logger_error}</code>"
                )
            except Exception:
                return

    @staticmethod
    async def _send_media_afk(
        client,
        message,
        media_type,
        file_id,
        caption,
        entities,
        effect_id=None,
    ):
        pre_senders = {
            "photo": bot.send_photo,
            "voice": bot.send_voice,
            "audio": bot.send_audio,
            "video": bot.send_video,
            "animation": bot.send_animation,
            "document": bot.send_document,
            "sticker": bot.send_sticker,
            "video_note": bot.send_video_note,
        }
        reply_senders = {
            "photo": message.reply_photo,
            "voice": message.reply_voice,
            "audio": message.reply_audio,
            "video": message.reply_video,
            "animation": message.reply_animation,
            "document": message.reply_document,
            "sticker": message.reply_sticker,
            "video_note": message.reply_video_note,
        }
        file_attrs = {
            "photo": "photo",
            "voice": "voice",
            "audio": "audio",
            "video": "video",
            "animation": "animation",
            "document": "document",
            "sticker": "sticker",
            "video_note": "video_note",
        }
        try:
            if media_type not in pre_senders:
                return await message.reply(
                    "<b>Error:</b> Tipe media AFK tidak didukung."
                )
            # Kirim file userbot ke bot agar mendapat file_id bot.
            temporary_message = await pre_senders[media_type](client.me.id, file_id)
            new_file_id = None
            async for media in client.search_messages(bot.username, limit=1):
                media_object = getattr(media, file_attrs[media_type], None)
                if media_object:
                    new_file_id = getattr(media_object, "file_id", None)
                break
            if not new_file_id:
                try:
                    await bot.delete_messages(bot.username, temporary_message.id)
                except Exception:
                    pass
                return await message.reply(
                    "<b>Error:</b> Data media AFK tidak ditemukan."
                )
            kwargs = {"reply_to_message_id": message.id}
            if effect_id:
                kwargs["effect_id"] = effect_id
            if media_type not in ("sticker", "video_note"):
                kwargs["caption"] = caption
                kwargs["caption_entities"] = entities
            sent = await reply_senders[media_type](new_file_id, **kwargs)
            try:
                await bot.delete_messages(bot.username, temporary_message.id)
            except Exception:
                pass
            return sent
        except Exception:
            return await message.reply(
                f"<b>Send failed:</b><code>{traceback.format_exc()}</code>"
            )

    @staticmethod
    async def unset_afk(client, message):
        emo = Emoji(client)
        await emo.get()
        afk_data = await dB.get_var(client.me.id, "AFK")
        if not afk_data:
            return
        async for last_message in client.get_chat_history(message.chat.id):
            if last_message.reply_markup:
                try:
                    await last_message.delete()
                except Exception:
                    pass
        await dB.remove_var(client.me.id, "AFK")
        afk_text = f"<b>{emo.sukses} Back to Online!!</b>"
        try:
            online_message = await message.reply(afk_text)
            await asyncio.sleep(3)
            return await online_message.delete()
        except Exception:
            return
