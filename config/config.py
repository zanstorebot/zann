import json
import os
import sys
from base64 import b64decode

import requests
from dotenv import load_dotenv


def get_blacklist():
    try:
        aa = "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL25heWExNTAzL3dhcm5pbmcvbWFpbi9ibGdjYXN0Lmpzb24="
        bb = b64decode(aa).decode("utf-8")
        res = requests.get(bb)
        if res.status_code == 200:
            return json.loads(res.text)
    except Exception as e:
        sys.exit(1)


load_dotenv()

HELPABLE = {}

DICT_BUTTON = {}

COPY_ID = {}

NAMA_CORE = "ZanStore Core v3.9"
WAJIB_JOIN = ["Lspacefams", "alicedevspro", "alicesuprot", "zannstre"]
USENAME_OWNER = os.environ.get("USENAME_OWNER", "@fauzanthrq")
API_ID = int(os.environ.get("API_ID", 38396733))
MAX_BOT = int(os.environ.get("MAX_BOT", 50))

API_HASH = os.environ.get("API_HASH", "de8ba979c9f9ad1c0e74e7d8a5560c3a")

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8964070527:AAG-vesNO93FkcjcNDhRO_heb4my9COPlz8"
)

BOT_ID = BOT_TOKEN.split(":")[0]

IMG_HOST_URL = os.environ.get("IMG_HOST_URL", "http://103.190.0.119:8088")
IMG_HOST_PORT = int(os.environ.get("IMG_HOST_PORT", 8088))

API_GEMINI = os.environ.get("API_GEMINI", "AIzaSyDV1VmVmTbB5ESZbzIMa_g0v05BFUXDOII")

API_NEOX = os.environ.get("API_NEOX", "alicedevcode")

API_BOTCHAX = os.environ.get("API_BOTCHAX", "zann")

API_MAELYN = os.environ.get("API_MAELYN", "sk_ms_d3d4e5861511d73ddd7bda4c958d0daabd5d5793638e120c")

BOT_NAME = os.environ.get("BOT_NAME", "AutoPayzan")

DB_NAME = os.environ.get("DB_NAME", "ZandB")

URL_LOGO = os.environ.get("URL_LOGO", "https://u.pone.rs/tlszrldr.jpg")

BLACKLIST_GCAST = get_blacklist()

SUDO_OWNERS = list(
    map(
        int,
        os.environ.get(
            "SUDO_OWNERS",
            "8659619672 2114557671 8546938757 8713820679",
        ).split(),
    )
)
DEVS = list(
    map(
        int,
        os.environ.get(
            "DEVS",
            "8659619672 2114557671 8713820679 8546938757",
        ).split(),
    )
)

AKSES_DEPLOY = list(
    map(int, os.environ.get("AKSES_DEPLOY", "8659619672 2114557671 8546938757").split())
)

OWNER_ID = int(os.environ.get("OWNER_ID", 8546938757))

LOG_SELLER = int(os.environ.get("LOG_SELLER", -1004461472898))

LOG_BACKUP = int(os.environ.get("LOG_BACKUP", -1004461472898))

SPOTIFY_CLIENT_ID = os.environ.get(
    "SPOTIFY_CLIENT_ID", "e09ff7a19b204b62b6048a73bd605fe6"
)
SPOTIFY_CLIENT_SECRET = os.environ.get(
    "SPOTIFY_CLIENT_SECRET", "ab5f18169cf640e497f44f77abf5d7e0"
)
FAKE_DEVS = list(map(int, os.environ.get("FAKE_DEVS", "8546938757").split()))

CASAKU_BASE_URL = os.environ.get("CASAKU_BASE_URL", "https://api.casaku.id")
CASAKU_LICENSE_KEY = os.environ.get("CASAKU_LICENSE_KEY", "cashify_144e6d6ca8226e7ea82378fd4d76e9fde47eb912873f6e8353d92a5e781786e0")

# ID QRIS yang sudah terdaftar di Casaku
CASAKU_QRIS_ID = os.environ.get("CASAKU_QRIS_ID", "fd866e6e-a9aa-4723-aa16-ac7dea1c8bff")

# Package ID Casaku
CASAKU_PACKAGE_IDS = os.environ.get("CASAKU_PACKAGE_IDS", "id.dana")



CODEQR = os.environ.get(
    "CODEQR",
    "00020101021126570011ID.DANA.WWW011893600915382885122502098288512250303UMI51440014ID.CO.QRIS.WWW0215ID10253733543370303UMI5204581253033605802ID5912Citra Geprek6015Kabupaten Dairi6105222146304BB48"
    )
    


DEVA = [8659619672, 2114557671, 8546938757, 8713820679]
if OWNER_ID not in SUDO_OWNERS:
    SUDO_OWNERS.append(OWNER_ID)
if OWNER_ID not in DEVS:
    DEVS.append(OWNER_ID)
if OWNER_ID not in FAKE_DEVS:
    FAKE_DEVS.append(OWNER_ID)
for P in FAKE_DEVS:
    if P not in DEVS:
        DEVS.append(P)
    if P not in SUDO_OWNERS:
        SUDO_OWNERS.append(P)