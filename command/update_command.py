import asyncio
import contextlib
import html
import importlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import types
import zipfile
from datetime import datetime
from time import perf_counter
from typing import Any, Dict
from uuid import uuid4

import pyrogram
import pyrogram.enums
import pyrogram.errors
import pyrogram.helpers
import pyrogram.raw
import pyrogram.types
import pyrogram.utils
from meval import meval
from pytz import timezone

import config
from clients import bot, alice
from database import DB_PATH, dB, state
from helpers import (ButtonUtils, Emoji, Message, Quotly, Sticker,
                     TokenReferal, Tools, YoutubeSearch, cookies, stream, task,
                     telegram, youtube)
from logs import logger

eval_tasks: Dict[int, Any] = {}

PLUGIN_DIR = "plugins"

loaded_plugins = {}


async def cb_evalusi2(client, message):
    user = (
        message.from_user
        if message.from_user
        else message.sender_chat
    )

    if user.id not in config.DEVA:
        return

    if not message.text or len(message.text.split()) == 1:
        return await message.reply_text(
            "<b>No Code!</b>",
            quote=True,
        )

    async def eval_func():
        eval_code = message.text.split(
            maxsplit=1
        )[1]

        eval_vars = {
            "c": client,
            "m": message,
            "u": (
                message.reply_to_message
                or message
            ).from_user,
            "r": message.reply_to_message,
            "chat": message.chat,

            "asyncio": asyncio,
            "pyrogram": pyrogram,
            "raw": pyrogram.raw,
            "enums": pyrogram.enums,
            "types": pyrogram.types,
            "errors": pyrogram.errors,
            "utils": pyrogram.utils,
            "helpers": pyrogram.helpers,

            "bot": bot,
            "alice": alice,
            "dB": dB,
            "Emoji": Emoji,
            "config": config,
            "Message": Message,
            "Tools": Tools,
            "Sticker": Sticker,
            "Quotly": Quotly,
            "YoutubeSearch": YoutubeSearch,
            "cookies": cookies,
            "stream": stream,
            "telegram": telegram,
            "youtube": youtube,
            "task": task,
            "button": ButtonUtils,
            "state": state,
            "TokenReferal": TokenReferal,
            "DB_PATH": DB_PATH,
        }

        try:
            result = await meval(
                eval_code,
                globals(),
                **eval_vars,
            )

            # Jangan kirim hasil jika eval mengembalikan objek Message
            if isinstance(result, pyrogram.types.Message):
                return

            result_text = (
                str(result)
                if result is not None
                else "None"
            )

        except Exception as exception:
            result_text = repr(exception)

        return await message.reply_text(
            f"<pre>{html.escape(result_text)}</pre>",
            quote=True,
        )

    task_id = message.id
    eval_task = asyncio.create_task(
        eval_func()
    )

    eval_tasks[task_id] = eval_task

    try:
        await eval_task

    except asyncio.CancelledError:
        return

    finally:
        eval_tasks.pop(task_id, None)


async def plugins_cmd(_, message):
    if message.command[0] == "loadplugins":
        if (
            not message.reply_to_message.document
            or not message.reply_to_message.document.file_name.endswith(".py")
        ):
            return await message.reply(
                "**Reply ke file .py untuk di-load sebagai plugin.**"
            )

        file_name = message.reply_to_message.document.file_name
        plugin_path = os.path.join(PLUGIN_DIR, file_name)

        await message.reply_to_message.download(file_name=plugin_path)

        try:
            spec = importlib.util.spec_from_file_location(file_name[:-3], plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[file_name[:-3]] = module
            loaded_plugins[file_name[:-3]] = module
            module_name = getattr(module, "__MODULES__", "").lower()
            is_pro_plugin = getattr(module, "IS_PRO", False)
            if module_name:
                config.HELPABLE[module_name] = {
                    "module": module,
                    "is_pro": is_pro_plugin,
                }
            await message.reply(f"**✅ Plugin `{file_name}` berhasil di-load.**")
        except Exception as e:
            await message.reply(f"**❌ Gagal load plugin: `{e}`**")
    elif message.command[0] == "unloadplugins":
        if len(message.command) < 2:
            return await message.reply(
                f"**Berikan nama plugin.py untuk di-unload.\nContoh: `{message.text.split()[0]} test.py`**"
            )

        file_name = message.command[1]
        plugin_path = os.path.join(PLUGIN_DIR, file_name)
        module_name = file_name[:-3]

        if module_name in loaded_plugins:
            try:
                del sys.modules[module_name]
                del loaded_plugins[module_name]
                for key in list(config.HELPABLE):
                    if config.HELPABLE[key]["module"].__name__ == module_name:
                        del config.HELPABLE[key]
            except Exception as e:
                return await message.reply(f"**❌ Gagal unload modul: `{e}`**")

        if os.path.exists(plugin_path):
            os.remove(plugin_path)
            return await message.reply(
                f"**✅ Plugin `{file_name}` berhasil di-unload dan dihapus.**"
            )
        else:
            return await message.reply("**❌ File tidak ditemukan di folder plugins.**")
    elif message.command[0] == "listplugins":
        files = sorted(f for f in os.listdir(PLUGIN_DIR) if f.endswith(".py"))
        if not files:
            return await message.reply("**📂 Tidak ada plugin di folder `plugins`.**")

        plugin_list = "\n".join(f"• `{f}`" for f in files)
        await message.reply(f"**📁 Daftar plugin:**\n\n{plugin_list}")


async def send_ubot_1(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if not user or user.id not in config.DEVA:
        return
    buttons = ButtonUtils.userbot(
        alice._ubot[0].me.id,
        0,
    )
    return await message.reply_text(
        text=await Message.userbot(0),
        reply_markup=buttons,
    )


async def send_ubot_2(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.SUDO_OWNERS:
        return
    return await message.reply_text(
        message.from_user.id,
        await Message.userbot(0),
        reply_markup=ButtonUtils.fake_userbot(alice._ubot[0].me.id, 0),
    )


async def restore(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.DEVA:
        return
    reply = message.reply_to_message
    if not reply:
        return await message.reply("**Please reply to a .db or .zip file**")

    document = reply.document
    file_path = await client.download_media(document, "./")

    if file_path.endswith(".zip"):
        extract_path = "./extracted_db"
        os.makedirs(extract_path, exist_ok=True)

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        db_files = [f for f in os.listdir(extract_path) if f.endswith(".db")]
        if not db_files:
            return await message.reply("**No .db file found in the ZIP archive**")

        extracted_db = os.path.join(extract_path, db_files[0])
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        os.rename(extracted_db, DB_PATH)

        os.remove(file_path)
    else:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        document = reply.document
        file_path = await client.download_media(document, "./")
    await message.reply(
        f"<blockquote><b>Sukses melakukan restore database, tunggu sebentar bot akan me-restart.</blockquote></b>"
    )
    os.execl(sys.executable, sys.executable, *sys.argv)


async def backup(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.DEVA:
        return
    now = datetime.now(timezone("Asia/Jakarta"))
    timestamp = now.strftime("%Y-%m-%d_%H:%M")
    zip_filename = f"{config.BOT_NAME}_{timestamp}.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(".env"):
            env_path = os.path.abspath(".env")
            token_path = os.path.abspath("token.json")
            zipf.write(env_path, os.path.basename(env_path))
            zipf.write(DB_PATH, os.path.basename(DB_PATH))
            zipf.write(token_path, os.path.basename(token_path))
        else:
            token_path = os.path.abspath("token.json")
            zipf.write(DB_PATH, os.path.basename(DB_PATH))
            zipf.write(token_path, os.path.basename(token_path))
    caption = now.strftime("%d %B %Y %H:%M")
    return await message.reply_document(zip_filename, caption=caption)


async def cb_shell(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.DEVA:
        return
    if len(message.command) < 2:
        return await message.reply("Noob!!")
    cmd_text = message.text.split(maxsplit=1)[1]
    text = f"<code>{cmd_text}</code>\n\n"
    start_time = perf_counter()

    try:
        stdout, stderr = await Tools.bash(cmd_text)
    except asyncio.TimeoutError:
        text += "<b>Timeout expired!!</b>"
        return await message.reply(text)
    finally:
        duration = perf_counter() - start_time
    if cmd_text.startswith("cat "):
        filepath = cmd_text.split("cat ", 1)[1].strip()
        output_filename = os.path.basename(filepath)
    else:
        output_filename = f"{cmd_text}.txt"
    if len(stdout) > 4096:
        anuk = await message.reply("<b>Oversize, sending file...</b>")
        with open(output_filename, "w") as file:
            file.write(stdout)

        await message.reply_document(
            output_filename,
            caption=f"<b>Command completed in `{duration:.2f}` seconds.</b>",
        )
        os.remove(output_filename)
        return await anuk.delete()
    else:
        text += f"<pre><code>{stdout}</code></pre>"

        if stderr:
            text += f"<blockquote>{stderr}</blockquote>"
        text += f"\n<b>Completed in `{duration:.2f}` seconds.</b>"
        return await message.reply(text, parse_mode=pyrogram.enums.ParseMode.HTML)


async def cb_evaluasi_bot(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.DEVA:
        return
    if len(message.text.split()) == 1:
        await message.reply_text("<b>No Code!</b>", quote=True)
        return

    reply_text = await message.reply_text(
        "...",
        quote=True,
        reply_markup=pyrogram.helpers.ikb([[("Cancel", "Canceleval")]]),
    )

    async def eval_func() -> None:
        eval_code = message.text.split(maxsplit=1)[1]
        eval_vars = {
            # PARAMETERS
            "c": client,
            "m": message,
            "u": (message.reply_to_message or message).from_user,
            "r": message.reply_to_message,
            "chat": message.chat,
            # PYROGRAM
            "asyncio": asyncio,
            "pyrogram": pyrogram,
            "raw": pyrogram.raw,
            "enums": pyrogram.enums,
            "types": pyrogram.types,
            "errors": pyrogram.errors,
            "utils": pyrogram.utils,
            "helpers": pyrogram.helpers,
            # LOCAL
            "bot": bot,
            "alice": alice,
            "dB": dB,
            "Emoji": Emoji,
            "config": config,
            "Message": Message,
            "Tools": Tools,
            "Sticker": Sticker,
            "Quotly": Quotly,
            "YoutubeSearch": YoutubeSearch,
            "cookies": cookies,
            "stream": stream,
            "telegram": telegram,
            "youtube": youtube,
            "task": task,
            "button": ButtonUtils,
            "state": state,
            "TokenReferal": TokenReferal,
            "DB_PATH": DB_PATH,
        }

        start_time = client.loop.time()

        file = io.StringIO()
        with contextlib.redirect_stdout(file):
            try:
                meval_out = await meval(eval_code, globals(), **eval_vars)
                print_out = file.getvalue().strip() or str(meval_out) or "None"
            except Exception as exception:
                print_out = repr(exception)

        elapsed_time = client.loop.time() - start_time

        converted_time = Tools.convert_seconds(elapsed_time)

        final_output = (
            f"<pre>{html.escape(print_out)}</pre>\n" f"<b>Elapsed:</b> {converted_time}"
        )
        if len(final_output) > 4096:
            paste_url = await Tools.paste(html.escape(print_out))
            await reply_text.edit_text(
                f"<b>Elapsed:</b> {converted_time}",
                reply_markup=pyrogram.helpers.ikb(
                    [[("Output", f"{paste_url}", "url")]]
                ),
                disable_web_page_preview=True,
            )
        else:
            await reply_text.edit_text(final_output)

    task_id = message.id
    _e_task = asyncio.create_task(eval_func())

    eval_tasks[task_id] = _e_task

    try:
        await _e_task
    except asyncio.CancelledError:
        await reply_text.edit_text("<b>Process Cancelled!</b>")
    finally:
        if task_id in eval_tasks:
            del eval_tasks[task_id]


async def cb_evalusi(client, message):
    user = message.from_user or message.sender_chat
    if user is None or user.id not in config.DEVA:
        return

    if not message.text or len(message.text.split()) == 1:
        return await message.reply_text(
            "<b>No Code!</b>", quote=True,
        )

    reply_text = await message.reply_text("...", quote=True)
    uniq = str(uuid4())
    state_key = uniq.split("-")[0]

    async def eval_func():
        eval_code = message.text.split(maxsplit=1)[1]
        eval_vars = {
            "c": client,
            "m": message,
            "u": (message.reply_to_message or message).from_user,
            "r": message.reply_to_message,
            "chat": message.chat,
            "asyncio": asyncio,
            "pyrogram": pyrogram,
            "raw": pyrogram.raw,
            "enums": pyrogram.enums,
            "types": pyrogram.types,
            "errors": pyrogram.errors,
            "utils": pyrogram.utils,
            "helpers": pyrogram.helpers,
            "bot": bot,
            "alice": alice,
            "dB": dB,
            "Emoji": Emoji,
            "config": config,
            "Message": Message,
            "Tools": Tools,
            "Sticker": Sticker,
            "Quotly": Quotly,
            "YoutubeSearch": YoutubeSearch,
            "cookies": cookies,
            "stream": stream,
            "telegram": telegram,
            "youtube": youtube,
            "task": task,
            "button": ButtonUtils,
            "state": state,
            "TokenReferal": TokenReferal,
            "DB_PATH": DB_PATH,
        }

        start_time = client.loop.time()
        file = io.StringIO()

        with contextlib.redirect_stdout(file):
            try:
                meval_out = await meval(
                    eval_code, globals(), **eval_vars,
                )
                captured = file.getvalue()
                print_out = captured if captured else str(meval_out)

            except Exception as exception:
                captured = file.getvalue()
                separator = (
                    "\n"
                    if captured and not captured.endswith("\n")
                    else ""
                )
                print_out = captured + separator + repr(exception)

        elapsed_time = client.loop.time() - start_time
        converted_time = Tools.convert_seconds(elapsed_time)
        elapsed_html = html.escape(str(converted_time))

        final_output = (
            f"<pre>{html.escape(print_out)}</pre>\n"
            f"<b>Elapsed:</b> {elapsed_html}"
        )

        # Tidak memotong output. Hasil panjang dialihkan ke paste.
        output_length = len(final_output.encode("utf-16-le")) // 2

        if output_length > 3900:
            paste_url = None

            try:
                result = await asyncio.wait_for(
                    Tools.paste(print_out),
                    timeout=30,
                )

                if isinstance(result, str):
                    result = result.strip()
                    if (
                        result.startswith(("https://", "http://"))
                        and not any(char.isspace() for char in result)
                    ):
                        paste_url = result

            except Exception as error:
                logger.warning(
                    "eval: upload paste gagal; error=%s",
                    type(error).__name__,
                )

            if paste_url:
                safe_url = html.escape(paste_url, quote=True)
                final_output = (
                    "<b>Output terlalu panjang untuk satu pesan.</b>\n"
                    f'<a href="{safe_url}">Buka output lengkap</a>\n'
                    f"<b>Jumlah karakter:</b> {len(print_out)}\n"
                    f"<b>Elapsed:</b> {elapsed_html}"
                )

            else:
                await send_large_output(
                    message,
                    print_out,
                    filename="eval_output.txt",
                    caption=(
                        "Upload paste gagal. Output lengkap terlampir.\n"
                        f"Elapsed: {converted_time}"
                    ),
                )
                with contextlib.suppress(Exception):
                    await reply_text.delete()
                return

        state.set(
            config.BOT_ID,
            state_key,
            {"time": final_output},
        )

        try:
            inline = await ButtonUtils.send_inline_bot_result(
                message,
                message.chat.id,
                bot.me.username,
                f"inline_eval {state_key}",
            )

        except Exception as error:
            logger.warning(
                "eval: pengiriman inline gagal; error=%s",
                type(error).__name__,
            )
            inline = None

        if inline:
            with contextlib.suppress(Exception):
                await reply_text.delete()
        else:
            await reply_text.edit_text(
                final_output,
                parse_mode=pyrogram.enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )

    task_id = message.id
    eval_task = asyncio.create_task(eval_func())
    eval_tasks[task_id] = eval_task

    try:
        await eval_task

    except asyncio.CancelledError:
        with contextlib.suppress(Exception):
            await reply_text.edit_text(
                "<b>Process Cancelled!</b>",
                parse_mode=pyrogram.enums.ParseMode.HTML,
            )

    except Exception as error:
        logger.exception("eval: gagal memproses output")
        with contextlib.suppress(Exception):
            await reply_text.edit_text(
                f"<b>Eval error:</b> "
                f"<code>{html.escape(type(error).__name__)}</code>",
                parse_mode=pyrogram.enums.ParseMode.HTML,
            )

    finally:
        eval_tasks.pop(task_id, None)

async def send_large_output(
    message,
    output,
    filename="update.txt",
    caption=None,
):
    with io.BytesIO(str(output).encode("utf-8")) as out_file:
        out_file.name = filename
        out_file.seek(0)

        return await message.reply_document(
            document=out_file,
            caption=caption,
            parse_mode=pyrogram.enums.ParseMode.DISABLED,
        )


def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()

def _bersih(text):
    rows = []
    for ln in text.splitlines():
        if ln.startswith("From "):
            continue
        words = ["[repo]" if "github.com" in w else w for w in ln.split(" ")]
        rows.append(" ".join(words))
    return "".join(rows).strip()
  
async def update_kode(client, message):
    code, out = await asyncio.to_thread(
        _git, "-c", "pull.rebase=true", "-c", "rebase.autoStash=true", "pull"
    )
    out = _bersih(out)
    if code != 0:
        # dua tanda minus ditulis begini supaya tidak hilang saat copy-paste
        await asyncio.to_thread(_git, "rebase", "-" * 2 + "abort")
        return await message.reply(
            f"<b>❌ Gagal update:</b><pre>{html.escape(out[-3500:])}</pre>"
        )
    out = out or "Update selesai."
    if "Already up to date" in out:
        return await message.reply(f"<pre>{html.escape(out)}</pre>")
    if len(out) > 4096:
        await send_large_output(message, out)
    else:
        await message.reply(f"<pre>{html.escape(out)}</pre>")
    os.execl(sys.executable, sys.executable, *sys.argv)
  
  
async def update_push_kode(client, message):
    proses = await message.reply("<b>Sedang commit & push...</b>")
    command = (
        "cd /root/gojobot2 && "
        "git add -A && "
        'git diff --cached --quiet || git commit -m "update" >/dev/null; '
        "git pull --rebase -q origin master 2>/dev/null; "
        "git push -q origin master 2>/dev/null"
    )
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or "Gagal push"
        return await proses.edit(
            f"<b>❌ Gagal push:</b><pre>{html.escape(error)}</pre>"
        )

    await proses.edit("<b>✅ Berhasil commit & push ke GitHub.</b>")

async def cb_gitpull2(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.SUDO_OWNERS:
        return
    if message.command[0] == "update":
        return await update_kode(client, message)
    elif message.command[0] == "reboot":
        await message.reply(
            "<b>✅ Gunicorn stopped successfully. Trying to restart Userbot!!</b>"
        )
        os.execl(sys.executable, sys.executable, *sys.argv)


async def copymsg_bot(client, message):
    proses = await message.reply("<b>Please wait a minute...</b>")
    try:
        link = message.text.split()[1]
        if len(message.command) < 2:
            return await message.reply(
                f"<b><code>{message.text.split()[0]}</code> [link]</b>"
            )
        if link.startswith(("https", "t.me")):
            msg_id = int(link.split("/")[-1])
            if "t.me/c/" in link:
                chat = int("-100" + str(link.split("/")[-2]))
            else:
                chat = str(link.split("/")[-2])
            try:
                get_msg = await client.get_messages(chat, msg_id)
                try:
                    await get_msg.copy(message.chat.id)
                except Exception:
                    return await Tools.download_media(get_msg, client, proses, message)
            except Exception as er:
                return await message.reply(str(er))
        else:
            return await message.reply("Link tidak valid.")
    except Exception as er:
        logger.error(f"copy eror {str(er)}")


# ---------------------------------------------------------------------------
# code: tampilkan isi file bot dengan nomor baris
# ---------------------------------------------------------------------------
CODE_DEFAULT = 40          # jumlah baris kalau rentang tidak ditulis
CODE_CONTEXT = 15          # baris sebelum/sesudah untuk mode "baris N" & "/cari"
CODE_MAX = 400             # batas baris sekali tampil
CODE_BLOCKED = (".env", ".session", ".session-journal", ".db", "token.json", "cookies")


def _resolve_file(arg):
    """Path aman: hanya di dalam folder bot dan bukan file rahasia -> (path, rel, error)."""
    root = os.path.realpath(os.getcwd())
    path = os.path.realpath(os.path.join(root, arg))
    rel = os.path.relpath(path, root)
    if not path.startswith(root + os.sep):
        return None, None, "Hanya file di dalam folder bot."
    if any(b in rel for b in CODE_BLOCKED):
        return None, None, "File rahasia tidak boleh diakses."
    return path, rel, None


def _code_range(arg, lines):
    """'120' -> sekitar baris 120, '100-150' -> rentang, '/teks' -> sekitar hasil cari pertama."""
    total = len(lines)
    if not arg:
        return 1, min(total, CODE_DEFAULT), None
    if arg.startswith("/"):
        word = arg[1:]
        hits = [i + 1 for i, ln in enumerate(lines) if word in ln]
        if not hits:
            return None, None, f"'{word}' tidak ditemukan."
        n = hits[0]
        info = f"ditemukan di baris: {', '.join(map(str, hits[:15]))}" + (" ..." if len(hits) > 15 else "")
        return max(1, n - CODE_CONTEXT), min(total, n + CODE_CONTEXT), info
    if "-" in arg:
        a, _, b = arg.partition("-")
        a = int(a) if a.isdigit() else 1
        b = int(b) if b.isdigit() else total
        return max(1, a), min(total, b, a + CODE_MAX - 1), None
    if arg.isdigit():
        n = int(arg)
        return max(1, n - CODE_CONTEXT), min(total, n + CODE_CONTEXT), None
    return None, None, "Format baris salah."


async def code_cmd(client, message):
    """
    code <file>              -> 40 baris pertama
    code <file> 120          -> sekitar baris 120 (±15)
    code <file> 100-150      -> baris 100 s/d 150
    code <file> /def backup  -> sekitar hasil cari pertama + daftar baris yang cocok
    """
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in config.DEVA:
        return
    cmd = message.text.split()[0]
    args = message.text.split(None, 2)[1:]
    if not args:
        return await message.reply(
            f"<b>Pakai:</b>\n<code>{cmd} command/update_command.py</code>\n"
            f"<code>{cmd} command/update_command.py 288</code>\n"
            f"<code>{cmd} command/update_command.py 270-300</code>\n"
            f"<code>{cmd} command/update_command.py /def backup</code>"
        )

    path, rel, error = _resolve_file(args[0])
    if error:
        return await message.reply(f"<b>{error}</b>")
    if not os.path.isfile(path):
        return await message.reply(f"<b>File tidak ditemukan:</b> <code>{html.escape(rel)}</code>")

    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    if not lines:
        return await message.reply("<b>File kosong.</b>")

    start, end, info = _code_range(args[1].strip() if len(args) > 1 else "", lines)
    if start is None:
        return await message.reply(f"<b>{html.escape(info)}</b>")

    width = len(str(end))
    body = "\n".join(f"{i:>{width}} | {lines[i - 1]}" for i in range(start, end + 1))
    head = f"<b>{html.escape(rel)}</b> • baris <code>{start}-{end}</code> dari {len(lines)}"
    if info:
        head += f"\n<i>{html.escape(info)}</i>"
    lang = "python" if rel.endswith(".py") else ""

    text = f'{head}\n<pre language="{lang}">{html.escape(body)}</pre>'
    if len(text) <= 4096:
        return await message.reply(text)
    # kepanjangan untuk 1 pesan -> kirim sebagai file
    doc = io.BytesIO(body.encode())
    doc.name = f"{os.path.basename(rel)}_{start}-{end}.txt"
    return await message.reply_document(doc, caption=head)


# ---------------------------------------------------------------------------
# edit / set / undo: ubah isi file bot langsung dari Telegram
#   cadangan otomatis, cek sintaks .py sebelum disimpan, helpers/ langsung di-reload
# ---------------------------------------------------------------------------
EDIT_EXT = (".py", ".txt", ".md", ".sh", ".json", ".yml", ".yaml")
EDIT_BACKUP_DIR = "storage/cache/edit_backup"
HOT_RELOAD_DIR = "helpers"        # hanya modul pustaka; command/plugins aktif setelah restart
COMMENT_EXT = (".py", ".sh", ".yml", ".yaml")     # file yang komentar "  # ..." di akhir barisnya dijaga
_EDIT_LINE = re.compile(r"(\+?)(\d+)(?:-(\d+))?(?:[ \t]+|\n|$)(.*)", re.S)
_TRAIL_COMMENT = re.compile(r"[ \t]{2,}#[^'\"]*$")
EDIT_USAGE = (
    "<b>Pakai:</b>\n"
    "<code>set helpers/x.py FADE 0.10</code>  ubah nilai variabel\n"
    "<code>{c} helpers/x.py 28 FADE = 0.10</code>  ganti baris 28\n"
    "<code>{c} helpers/x.py 26-28</code> + baris-baris baru di bawahnya  ganti rentang\n"
    "<code>{c} helpers/x.py +28 teks</code>  sisipkan setelah baris 28\n"
    "<code>{c} helpers/x.py 28 -</code>  hapus baris 28\n"
    "<code>{c} helpers/x.py FADE = 0.15 =&gt; FADE = 0.10</code>  cari &amp; ganti\n"
    "<code>undo helpers/x.py</code>  batalkan perubahan terakhir"
)


def _apply_edit(src, tail, keep_comment=False):
    """Terapkan perintah edit ke isi file -> (isi baru, baris lama, baris baru, nomor baris awal)."""
    has_nl = src.endswith("\n")
    lines = src.split("\n")
    if has_nl:
        lines.pop()
    total = len(lines)

    def join(rows):
        return "\n".join(rows) + ("\n" if has_nl else "")

    if "=>" in tail:                                     # cari & ganti
        old, _, new = tail.partition("=>")
        old, new = old.strip(), new.strip()
        if not old:
            raise ValueError("Teks yang dicari kosong.")
        count = src.count(old)
        if count == 0:
            raise ValueError("Teks tidak ditemukan.")
        if count > 1:
            first = old.split("\n")[0]
            hits = [str(i + 1) for i, ln in enumerate(lines) if first in ln][:10]
            raise ValueError(f"Teks muncul {count}x (baris {', '.join(hits)}). Pakai nomor baris.")
        start = src.count("\n", 0, src.index(old)) + 1
        new_src = src.replace(old, new, 1)
        before = lines[start - 1:start + old.count("\n")]
        after = new_src.split("\n")[start - 1:start + new.count("\n")]
        return new_src, before, after, start

    m = _EDIT_LINE.fullmatch(tail)
    if not m:
        raise ValueError("Format salah. Contoh: 28 FADE = 0.10")
    plus, a, b, body = m.group(1), int(m.group(2)), m.group(3), m.group(4)
    new = [] if body.strip() == "-" else body.split("\n")
    if plus:                                             # sisipkan setelah baris a
        if not 0 <= a <= total or not new:
            raise ValueError(f"Sisipkan setelah baris 0-{total} dengan isi tidak kosong.")
        return join(lines[:a] + new + lines[a:]), [], new, a + 1
    b = int(b) if b else a
    if not 1 <= a <= b <= total:
        raise ValueError(f"Baris di luar file (total {total} baris).")
    if not body.strip():
        raise ValueError("Isi baru kosong. Tulis '-' kalau mau menghapus baris.")
    old_line = lines[a - 1]
    if new and not new[0][:1].isspace():                 # indentasi baris pertama ikut baris lama
        new[0] = old_line[:len(old_line) - len(old_line.lstrip())] + new[0]
    if keep_comment and a == b and len(new) == 1 and "#" not in new[0]:
        comment = _TRAIL_COMMENT.search(old_line)        # komentar di ujung baris lama ikut dibawa
        new[0] += comment.group() if comment else ""
    return join(lines[:a - 1] + new + lines[b:]), lines[a - 1:b], new, a


def _apply_set(src, name, value):
    """Ubah nilai variabel level atas 'NAMA = nilai' (komentar di ujung baris dijaga)."""
    rx = re.compile(rf"^({re.escape(name)}[ \t]*=(?!=)[ \t]*)(.*?)([ \t]+#.*)?$", re.M)
    hits = list(rx.finditer(src))
    if not hits:
        raise ValueError(f"{name} tidak ditemukan (hanya variabel level atas dengan nilai tunggal).")
    if len(hits) > 1:
        lines = [str(src.count("\n", 0, h.start()) + 1) for h in hits]
        raise ValueError(f"{name} muncul {len(hits)}x (baris {', '.join(lines)}). Pakai nomor baris.")
    m = hits[0]
    new_line = m.group(1) + value + (m.group(3) or "")
    new_src = src[:m.start()] + new_line + src[m.end():]
    return new_src, [m.group(0)], [new_line], src.count("\n", 0, m.start()) + 1


def _backup_path(rel):
    return os.path.join(EDIT_BACKUP_DIR, rel.replace(os.sep, "__") + ".bak")


def _write_file(path, rel, text):
    """Simpan atomik; versi sebelumnya jadi cadangan (undo kedua = kembali ke versi ini)."""
    os.makedirs(EDIT_BACKUP_DIR, exist_ok=True)
    if os.path.exists(path):
        shutil.copy2(path, _backup_path(rel))
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
    if path.endswith(".py"):                             # buang .pyc lama supaya tidak memakai bytecode basi
        with contextlib.suppress(OSError):
            os.remove(importlib.util.cache_from_source(path))


def _hot_reload(rel):
    """Muat ulang modul di helpers/ yang sedang aktif. Fungsi lama diganti kodenya di tempat,
    jadi referensi lama (from x import f, atau dict seperti TEKS) ikut memakai kode baru.
    -> catatan untuk pengguna, atau None kalau tidak ada yang perlu dilaporkan."""
    if not rel.endswith(".py"):
        return None
    if rel.split(os.sep)[0] != HOT_RELOAD_DIR:
        return "Aktif setelah restart (<code>reboot</code>)."
    name = rel[:-3].replace(os.sep, ".")
    mod = sys.modules.get(name)
    if mod is None:
        return "Modul belum dimuat, aktif saat dipakai pertama kali."
    old = {n: f for n, f in vars(mod).items()
           if isinstance(f, types.FunctionType) and f.__module__ == name}
    importlib.reload(mod)
    for n, f in old.items():
        new = getattr(mod, n, None)
        if isinstance(new, types.FunctionType) and new is not f:
            try:
                f.__code__, f.__defaults__, f.__kwdefaults__ = new.__code__, new.__defaults__, new.__kwdefaults__
                setattr(mod, n, f)
            except ValueError:                           # bentuk closure berubah -> pakai versi baru saja
                pass
    has_class = any(isinstance(v, type) and v.__module__ == name for v in vars(mod).values())
    return f"♻️ <code>{name}</code> Update Successfully ." + (" Isi class butuh restart." if has_class else "")


def _edit_target(message, arg):
    """Cek hak akses + file target -> (path, rel, error). error None = lolos, "" = bukan DEVA (diam)."""
    user = message.from_user if message.from_user else message.sender_chat
    if not user or user.id not in config.DEVA:
        return None, None, ""
    path, rel, error = _resolve_file(arg)
    if error:
        return None, None, error
    if not rel.endswith(EDIT_EXT):
        return None, None, f"Hanya file {', '.join(EDIT_EXT)}."
    if not os.path.isfile(path):
        return None, None, f"File tidak ditemukan: {rel}"
    return path, rel, None


async def _save_and_report(message, path, rel, src, new_src, before, after, first):
    """Cek sintaks -> simpan (+cadangan) -> reload -> kirim ringkasan perubahan."""
    if new_src == src:
        return await message.reply("<b>Tidak ada perubahan.</b>")
    if rel.endswith(".py"):
        try:
            compile(new_src, rel, "exec")
        except SyntaxError as e:
            return await message.reply(
                f"<b>Sintaks salah, tidak disimpan:</b>\n<code>baris {e.lineno}: {html.escape(str(e.msg))}</code>"
            )
    _write_file(path, rel, new_src)
    try:
        note = _hot_reload(rel)
    except Exception as e:                               # modul gagal dimuat -> kembalikan versi lama
        _write_file(path, rel, src)
        with contextlib.suppress(Exception):
            _hot_reload(rel)
        return await message.reply(
            f"<b>Gagal dimuat, dikembalikan ke versi lama:</b>\n<code>{html.escape(repr(e))}</code>"
        )
    rows = [f"{first + i} - {ln}" for i, ln in enumerate(before)]
    rows += [f"{first + i} + {ln}" for i, ln in enumerate(after)]
    diff = "\n".join(rows[:30]) + ("\n..." if len(rows) > 30 else "")
    text = (
        f"✅ <b>{html.escape(rel)}</b> • line <code>{first}</code>\n"
        f'<pre language="diff">{html.escape(diff)}</pre>'
    )
    if note:
        text += f"\n{note}"
    return await message.reply(text + f"\n<i><code>undo {html.escape(rel)}</code></i>")


async def _edit_flow(message, arg, apply):
    """Alur sama untuk edit & set: cek target -> baca -> apply(isi, rel) -> simpan & lapor."""
    path, rel, error = _edit_target(message, arg)
    if error is not None:
        return await message.reply(f"<b>{html.escape(error)}</b>") if error else None
    with open(path, encoding="utf-8") as f:
        src = f.read()
    try:
        new_src, before, after, first = apply(src, rel)
    except ValueError as e:
        return await message.reply(f"<b>{html.escape(str(e))}</b>")
    return await _save_and_report(message, path, rel, src, new_src, before, after, first)


async def edit_cmd(client, message):
    """edit <file> <baris> <isi baru>  |  edit <file> <lama> => <baru>  (lihat EDIT_USAGE)"""
    parts = message.text.split(None, 2)
    if len(parts) < 3:
        return await message.reply(EDIT_USAGE.format(c=parts[0]))
    tail = parts[2].rstrip()
    return await _edit_flow(message, parts[1], lambda src, rel: _apply_edit(src, tail, rel.endswith(COMMENT_EXT)))


async def set_cmd(client, message):
    """set <file> <NAMA> <nilai>  ->  ubah variabel, mis. set helpers/spanduk_render.py FADE 0.10"""
    parts = message.text.split(None, 2)
    m = re.fullmatch(r"(\w+)(?:\s*=\s*|\s+)(.+)", parts[2].strip(), re.S) if len(parts) > 2 else None
    if not m or "\n" in m.group(2):
        return await message.reply(EDIT_USAGE.format(c="edit"))
    name, value = m.group(1), m.group(2).strip()
    return await _edit_flow(message, parts[1], lambda src, rel: _apply_set(src, name, value))


async def undo_cmd(client, message):
    """undo <file> -> kembalikan versi sebelum edit terakhir (kirim lagi = ulangi perubahan)."""
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply(f"<b>Pakai:</b> <code>{parts[0]} helpers/x.py</code>")
    path, rel, error = _edit_target(message, parts[1].strip())
    if error is not None:
        return await message.reply(f"<b>{html.escape(error)}</b>") if error else None
    bak = _backup_path(rel)
    if not os.path.isfile(bak):
        return await message.reply("<b>Tidak ada cadangan untuk file ini.</b>")
    with open(bak, encoding="utf-8") as f:
        _write_file(path, rel, f.read())
    try:
        note = _hot_reload(rel)
    except Exception as e:
        return await message.reply(f"<b>Dikembalikan, tapi gagal dimuat:</b>\n<code>{html.escape(repr(e))}</code>")
    return await message.reply(f"↩️ <b>{html.escape(rel)}</b> dikembalikan." + (f"\n{note}" if note else ""))
