import json
import os
import re
import uuid
from html import escape
from urllib.parse import urlsplit

import aiofiles

from helpers import Emoji, Tools, animate_proses
from logs import logger

BASE_URL = "https://api.siputzx.my.id"
PHOTO_ENDPOINTS = {
    "ektp": ("/api/canvas/ektp", "pas_photo"),
    "delete": ("/api/canvas/delete", "image"),
    "beautiful": ("/api/canvas/beautiful", "image"),
    "xnxx": ("/api/canvas/xnxx", "image"),
    "facepalm": ("/api/canvas/facepalm", "image"),
}
MAKER_INFO = {
    "ektp": ("<nama> <laki/perempuan>", "Reply user atau foto"),
    "delete": ("", "Reply user atau foto"),
    "beautiful": ("", "Reply user atau foto"),
    "xnxx": ("<judul>", "Reply user atau foto"),
    "facepalm": ("", "Reply user atau foto"),
    "sertifikat": ("<teks>", "Tanpa reply"),
    "ephoto360": ("<URL efek> | <teks>", "Tanpa reply"),
}
MAKER_MODES = tuple(MAKER_INFO)
EKTP_FIELDS = (
    "provinsi", "kota", "nik", "nama", "ttl", "jenis_kelamin",
    "golongan_darah", "alamat", "rt/rw", "kel/desa", "kecamatan",
    "agama", "status", "pekerjaan", "kewarganegaraan",
    "masa_berlaku", "terbuat", "pas_photo",
)
EKTP_DEFAULTS = {
    "provinsi": "JAWA SELATAN",
    "kota": "BIKINI BOTTOM",
    "nik": "112233445678902",
    "ttl": "Telegram, 20-32-1945",
    "golongan_darah": "C",
    "alamat": "Jl. Aspal No. 69",
    "rt/rw": "000/007",
    "kel/desa": "Konoha",
    "kecamatan": "Mutualan",
    "agama": "Atheis",
    "status": "Belum Lahir",
    "pekerjaan": "Admin Grup",
    "kewarganegaraan": "WNT",
    "masa_berlaku": "Selama Gak Deak",
    "terbuat": "02-32-1945",
}
GENDERS = {
    "laki": "Laki-laki", "laki-laki": "Laki-laki",
    "pria": "Laki-laki", "cowok": "Laki-laki",
    "perempuan": "Perempuan", "wanita": "Perempuan",
    "cewek": "Perempuan",
}
IMAGE_MIMES = {
    "jpg": "image/jpeg", "png": "image/png",
    "webp": "image/webp", "gif": "image/gif",
}


class MakerError(ValueError):
    pass


def _valid_url(value):
    if not isinstance(value, str):
        return False
    try:
        parts = urlsplit(value.strip())
        return (
            parts.scheme in ("https", "http") and bool(parts.hostname)
            and not parts.username and not parts.password
        )
    except ValueError:
        return False


def _image_extension(content):
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def _result_url(data, excluded=()):
    if isinstance(data, str):
        value = data.strip()
        return value if _valid_url(value) and value not in excluded else None
    if isinstance(data, dict):
        for key in (
            "imageUrl", "image_url", "image", "images", "download",
            "download_url", "output", "result", "results", "data", "url",
        ):
            value = _result_url(data.get(key), excluded)
            if value:
                return value
    elif isinstance(data, list):
        for item in data:
            value = _result_url(item, excluded)
            if value:
                return value
    return None


def _api_error(data):
    if not isinstance(data, dict):
        return "Server mengembalikan respons gagal."

    detail = str(data.get("error") or data.get("message") or "")
    missing = re.search(
        r"""Missing\s+["']([A-Za-z0-9_/-]+)["']\s+file""",
        detail, re.I,
    )
    if missing:
        return f'Server meminta file dengan field "{missing.group(1)}".'
    return "API mengembalikan status gagal; detail input tidak ditampilkan."


async def _read_image(response, excluded=(), depth=0):
    info = (
        f"{response.url.host}{response.url.path} "
        f"| HTTP {response.status_code}"
    )
    if not response.content.strip():
        raise MakerError(f"{info}: respons kosong.")

    if 200 <= response.status_code < 300:
        extension = _image_extension(response.content)
        if extension:
            return response.content, extension

    try:
        data = response.json()
    except ValueError:
        mime = response.headers.get("Content-Type", "tidak tersedia")
        raise MakerError(
            f"{info} | {mime}: respons bukan gambar atau JSON."
        ) from None

    if response.status_code == 405:
        raise MakerError(f"{info}: metode request tidak didukung endpoint.")

    if not 200 <= response.status_code < 300:
        raise MakerError(f"{info}: {_api_error(data)}")

    if isinstance(data, dict):
        state = data.get("state")
        if state is None:
            state = data.get("status")
        failed_code = data.get("code")
        if (
            data.get("status") is False
            or data.get("success") is False
            or str(state).lower() in ("failed", "error", "cancelled")
            or (
                isinstance(failed_code, int)
                and not isinstance(failed_code, bool)
                and failed_code >= 400
            )
        ):
            raise MakerError(f"{info}: {_api_error(data)}")

    result_url = _result_url(data, excluded)
    if not result_url:
        raise MakerError(f"{info}: JSON tidak berisi URL hasil gambar.")
    if depth >= 2:
        raise MakerError(f"{info}: terlalu banyak URL berantai tanpa gambar.")

    result = await Tools.fetch.get(
        result_url, timeout=90, follow_redirects=True,
    )
    return await _read_image(result, (*excluded, result_url), depth + 1)


async def _reply_photo(client, message):
    reply = message.reply_to_message
    if not reply:
        raise MakerError("Balas foto atau pesan user yang foto profilnya ingin dipakai.")

    target_path = f"maker_input_{uuid.uuid4().hex}.jpg"
    downloaded_path = None

    try:
        if reply.photo:
            photo_id = reply.photo.file_id
        else:
            if not reply.from_user:
                raise MakerError(
                    "Pesan tidak memiliki pengirim user. Balas foto atau pesan user biasa."
                )
            try:
                user = await client.get_users(reply.from_user.id)
            except Exception as exc:
                raise MakerError(
                    f"Gagal membaca profil user: {type(exc).__name__}."
                ) from None

            if not user.photo:
                raise MakerError(
                    "Foto profil user tidak tersedia untuk akun ini. Balas foto langsung."
                )
            photo_id = user.photo.big_file_id

        downloaded_path = await client.download_media(
            photo_id, file_name=target_path,
        )
        if not downloaded_path or not os.path.isfile(downloaded_path):
            raise MakerError("Foto gagal diunduh.")

        async with aiofiles.open(downloaded_path, "rb") as file:
            content = await file.read()

        if not content:
            raise MakerError("Foto yang diunduh kosong.")

        extension = _image_extension(content)
        if extension not in IMAGE_MIMES:
            raise MakerError("Foto harus berupa JPG, PNG, WebP, atau GIF.")

        return content, extension

    finally:
        for path in {target_path, downloaded_path}:
            if path and os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    logger.warning("Maker: gagal membersihkan foto input.")


async def _request_photo(client, message, mode, params):
    endpoint, field_name = PHOTO_ENDPOINTS[mode]
    content, extension = await _reply_photo(client, message)
    fields = {
        key: str(value) for key, value in params.items()
        if key not in ("image", "pas_photo")
    }
    return await Tools.fetch.post(
        BASE_URL + endpoint,
        data=fields,
        files={
            field_name: (
                f"photo.{extension}", content, IMAGE_MIMES[extension],
            ),
        },
        timeout=120,
    )


def _ektp_params(argument):
    if not argument.lstrip().startswith("{"):
        parts = argument.rsplit(None, 1)
        if len(parts) != 2:
            raise MakerError(
                "Format: maker ektp Nama Lengkap laki, sambil reply user/foto."
            )
        nama, gender = parts[0].strip(), parts[1].lower()
        if not nama or "|" in nama or gender not in GENDERS:
            raise MakerError(
                "Format tanpa |: maker ektp Nama Lengkap laki/perempuan."
            )
        return {
            **EKTP_DEFAULTS,
            "nama": nama,
            "jenis_kelamin": GENDERS[gender],
        }

    try:
        data = json.loads(argument)
    except json.JSONDecodeError:
        raise MakerError("JSON eKTP tidak valid.") from None
    if not isinstance(data, dict):
        raise MakerError("Data eKTP harus berupa JSON object.")

    unknown = sorted(set(data) - set(EKTP_FIELDS))
    if unknown:
        raise MakerError(f"Field tidak dikenal: {', '.join(unknown)}.")

    params = {
        key: str(value).strip() for key, value in data.items()
        if isinstance(value, (str, int)) and not isinstance(value, bool)
    }
    missing = [
        key for key in EKTP_FIELDS
        if key != "pas_photo" and not params.get(key)
    ]
    if missing:
        raise MakerError(f"Field eKTP belum diisi: {', '.join(missing)}.")
    if not re.fullmatch(r"\d{16}", params["nik"]):
        raise MakerError("NIK contoh pada JSON harus berupa string 16 digit.")

    params.pop("pas_photo", None)
    return params


async def maker_img_cmd(client, message):
    em = Emoji(client)
    await em.get()
    command = message.command or []
    prefix = command[0] if command else "maker"
    pros = file_path = None
    stage = "validasi perintah"

    async def gagal(detail):
        content = (
            f"{em.gagal}<b>Maker gagal:</b> "
            f"<code>{escape(str(detail)[:650])}</code>"
        )
        return (
            await pros.edit(content)
            if pros is not None else await message.reply(content)
        )

    try:
        if len(command) < 2:
            return await gagal(
                f"Mode: {', '.join(MAKER_MODES)}. "
                f"Contoh: {prefix} ektp Contoh Nama laki, sambil reply user/foto."
            )

        aliases = {"sertifikat-tolol": "sertifikat", "ephoto": "ephoto360"}
        mode = aliases.get(command[1].lower(), command[1].lower())
        if mode not in MAKER_MODES:
            return await gagal(f"Mode tidak dikenal. Pilih: {', '.join(MAKER_MODES)}.")

        raw = message.text or message.caption or ""
        parts = raw.split(None, 2)
        argument = parts[2].strip() if len(parts) == 3 else ""
        params, excluded = {}, ()

        if mode in PHOTO_ENDPOINTS and not message.reply_to_message:
            return await gagal("Balas foto atau pesan user untuk mengambil foto profilnya.")

        if mode == "ektp":
            params = _ektp_params(argument)
        elif mode == "xnxx":
            if not argument:
                return await gagal(
                    f"Format: {prefix} xnxx <judul>, sambil reply user/foto."
                )
            params = {"title": argument}
        elif mode == "sertifikat":
            if not argument:
                return await gagal(f"Format: {prefix} sertifikat <teks>.")
            endpoint, params = "/api/canvas/sertifikat-tolol", {"text": argument}
        elif mode == "ephoto360":
            effect_url, separator, text = argument.partition("|")
            effect_url, text = effect_url.strip(), text.strip()
            if not separator or not text or not _valid_url(effect_url):
                return await gagal(
                    f"Format: {prefix} ephoto360 <URL efek> | <teks>."
                )
            if urlsplit(effect_url).hostname not in (
                "en.ephoto360.com", "ephoto360.com", "www.ephoto360.com",
            ):
                return await gagal("URL efek harus berasal dari website Ephoto360.")
            endpoint = "/api/m/ephoto360"
            params = {"url": effect_url, "text1": text}
            excluded = (effect_url,)

        pros = await animate_proses(message, em.proses)
        if pros is None:
            return

        if mode in PHOTO_ENDPOINTS:
            stage = f"mengambil foto dan mengirim multipart {mode}"
            response = await _request_photo(client, message, mode, params)
        else:
            stage = f"request {endpoint}"
            response = await Tools.fetch.get(
                BASE_URL + endpoint,
                params=params,
                timeout=120,
                follow_redirects=True,
            )

        stage = "membaca hasil API"
        content, extension = await _read_image(response, excluded)

        stage = "menyimpan hasil"
        file_path = f"maker_{mode}_{uuid.uuid4().hex}.{extension}"
        async with aiofiles.open(file_path, "wb") as file:
            await file.write(content)

        stage = "mengirim hasil ke Telegram"
        caption = f"{em.sukses}<b>Berhasil membuat {escape(mode)}.</b>"
        if mode == "ektp":
            caption += "\n<b>Data fiktif untuk hiburan.</b>"

        if extension == "gif":
            await message.reply_animation(file_path, caption=caption)
        else:
            await message.reply_photo(file_path, caption=caption)

        stage = "menghapus pesan proses"
        return await pros.delete()

    except MakerError as exc:
        return await gagal(exc)
    except Exception as exc:
        return await gagal(f"Tahap {stage}: {type(exc).__name__}.")
    finally:
        if file_path and os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError:
                logger.warning("Maker: gagal membersihkan gambar hasil.")