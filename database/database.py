import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aioshutil
import aiosqlite
import pytz

from config import DB_NAME

jakarta_timezone = pytz.timezone("Asia/Jakarta")
DB_PATH = f"./{DB_NAME}.db"
ENV_PATH = f"./.env"
BACKUP_TIME = datetime.now(jakarta_timezone)
BACKUP_PATH = f"./{DB_NAME}_backup_{BACKUP_TIME}.db"


class DatabaseClient:
    def __init__(self) -> None:
        self.db_path = Path(DB_PATH)
        self.env_path = Path(ENV_PATH)
        self.db_backup = f"{DB_PATH}_{BACKUP_TIME}"
        self.db_backup_format = "zip"
        self.temp_dir = self.db_path.parent / "./output"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.chconnect = {}
        # cache tabel variabel: _id -> dict hasil json.loads kolom vars
        # (dibaca sangat sering oleh handler per-pesan; dihapus otomatis setiap ada tulis)
        self._vars_cache = {}
        self._vars_ver = {}

    async def initialize(self):
        """Initialize the database connection and tables"""
        await self.connect()
        await self._initialize_database()

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path, check_same_thread=False)

    async def _initialize_database(self):
        script = """
        CREATE TABLE IF NOT EXISTS user_prefixes (
            user_id INTEGER PRIMARY KEY,
            prefix TEXT
        );
        CREATE TABLE IF NOT EXISTS floods (
            gw INTEGER,
            user_id INTEGER,
            flood TEXT,
            PRIMARY KEY (gw, user_id)
        );
        CREATE TABLE IF NOT EXISTS variabel (
            _id INTEGER PRIMARY KEY,
            vars TEXT
        );
        CREATE TABLE IF NOT EXISTS expired (
            _id INTEGER PRIMARY KEY,
            expire_date TEXT
        );
        CREATE TABLE IF NOT EXISTS userdata (
            user_id INTEGER PRIMARY KEY,
            depan TEXT,
            belakang TEXT,
            username TEXT,
            mention TEXT,
            full TEXT,
            _id INTEGER
        );
        CREATE TABLE IF NOT EXISTS ubotdb (
            user_id TEXT PRIMARY KEY,
            session_string TEXT
        );
        CREATE TABLE IF NOT EXISTS channeldb (
            user_id INTEGER,
            chat_id INTEGER,
            mode INTEGER,
            PRIMARY KEY (user_id, chat_id)
        );
        """
        await self.conn.executescript(script)
        await self.conn.commit()

    async def ensure_connection(self):
        if self.conn is None:
            await self.connect()

    async def get_pref(self, user_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT prefix FROM user_prefixes WHERE user_id = ?", (user_id,)
            )
            result = await cursor.fetchone()
            return json.loads(result[0]) if result else [".", "-", "!", "+", "?"]

    async def set_pref(self, user_id, prefix):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO user_prefixes (user_id, prefix)
                VALUES (?, ?)
            """,
                (user_id, json.dumps(prefix)),
            )
        await self.conn.commit()

    async def rem_pref(self, user_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM user_prefixes WHERE user_id = ?", (user_id,)
            )
        await self.conn.commit()

    # ------------------------------------------------------------------ cache
    @staticmethod
    def _vkey(_id):
        try:
            return int(_id)
        except (TypeError, ValueError):
            return _id

    def _invalidate(self, _id=None):
        """Buang cache satu _id (atau semua kalau _id None) setelah data ditulis."""
        if _id is None:
            self._vars_cache.clear()
            self._vars_ver.clear()
            return
        key = self._vkey(_id)
        self._vars_cache.pop(key, None)
        self._vars_ver[key] = self._vars_ver.get(key, 0) + 1

    async def _load_vars(self, _id):
        """Isi kolom vars sebagai dict (dari cache kalau ada)."""
        key = self._vkey(_id)
        if key in self._vars_cache:
            return self._vars_cache[key]
        ver = self._vars_ver.get(key, 0)
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT vars FROM variabel WHERE _id = ?", (_id,))
            row = await cursor.fetchone()
        data = json.loads(row[0]) if row and row[0] else None
        # jangan simpan kalau ada penulisan selama query berjalan (hindari cache basi)
        if self._vars_ver.get(key, 0) == ver:
            self._vars_cache[key] = data
        return data

    async def set_var(self, bot_id, vars_name, value, query="vars"):
        await self.ensure_connection()
        json_value = json.dumps(value)
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO variabel (_id, vars)
                VALUES (?, json_set(COALESCE((SELECT vars FROM variabel WHERE _id = ?), '{}'), ?, ?))
                """,
                (bot_id, bot_id, f"$.{query}.{vars_name}", json_value),
            )
        await self.conn.commit()
        self._invalidate(bot_id)

    async def get_var(self, bot_id, vars_name, query="vars"):
        data = await self._load_vars(bot_id)
        if not data:
            return None
        value = (data.get(query) or {}).get(vars_name)
        try:
            value = json.loads(value) if isinstance(value, str) else value
        except json.JSONDecodeError:
            pass
        # salinan: kode pemanggil boleh mengubah hasilnya tanpa merusak cache
        return copy.deepcopy(value) if isinstance(value, (dict, list)) else value

    async def remove_var(self, bot_id, vars_name, query="vars"):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE variabel SET vars = json_remove(vars, ?) WHERE _id = ?
            """,
                (f"$.{query}.{vars_name}", bot_id),
            )
        await self.conn.commit()
        self._invalidate(bot_id)

    async def all_var(self, user_id, query="vars"):
        data = await self._load_vars(user_id)
        return copy.deepcopy(data.get(query)) if data else None

    async def rm_all(self, bot_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute("DELETE FROM variabel WHERE _id = ?", (bot_id,))
        await self.conn.commit()
        self._invalidate(bot_id)

    async def get_list_from_var(self, user_id, vars_name, query="vars"):
        await self.ensure_connection()
        vars_data = await self.get_var(user_id, vars_name, query)
        return [int(x) for x in str(vars_data).split()] if vars_data else []

    async def add_to_var(self, user_id, vars_name, value, query="vars"):
        await self.ensure_connection()
        vars_list = await self.get_list_from_var(user_id, vars_name, query)
        vars_list.append(value)
        await self.set_var(user_id, vars_name, " ".join(map(str, vars_list)), query)

    async def remove_from_var(self, user_id, vars_name, value, query="vars"):
        await self.ensure_connection()
        vars_list = await self.get_list_from_var(user_id, vars_name, query)
        if value in vars_list:
            vars_list.remove(value)
            await self.set_var(user_id, vars_name, " ".join(map(str, vars_list)), query)

    async def get_expired_date(self, user_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT expire_date FROM expired WHERE _id = ?", (user_id,)
            )
            result = await cursor.fetchone()
            return (
                datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f%z")
                if result and result[0]
                else None
            )

    async def set_expired_date(self, user_id, expire_date):
        if isinstance(expire_date, str):
            try:
                expire_date = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S.%f%z")
            except ValueError:
                expire_date = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S.%f")
                expire_date = expire_date.replace(tzinfo=timezone(timedelta(hours=7)))

        formatted_date = expire_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")

        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO expired (_id, expire_date) VALUES (?, ?)
                """,
                (user_id, formatted_date),
            )
        await self.conn.commit()

    async def rem_expired_date(self, user_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE expired SET expire_date = NULL WHERE _id = ?
            """,
                (user_id,),
            )
        await self.conn.commit()

    async def cek_userdata(self, user_id: int) -> bool:
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT 1 FROM userdata WHERE user_id = ?", (user_id,))
            result = await cursor.fetchone()
            return bool(result)

    async def get_userdata(self, user_id: int):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM userdata WHERE user_id = ?", (user_id,))
            result = await cursor.fetchone()

            if result:
                return {
                    "user_id": result[0],
                    "depan": result[1],
                    "belakang": result[2],
                    "username": result[3],
                    "mention": result[4],
                    "full": result[5],
                    "_id": result[6],
                }
            return None

    async def add_userdata(
        self, user_id: int, depan, belakang, username, mention, full, _id
    ):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO userdata (user_id, depan, belakang, username, mention, full, _id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (user_id, depan, belakang, username, mention, full, _id),
            )
        await self.conn.commit()

    async def add_ubot(self, user_id, session_string):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO ubotdb (user_id, session_string)
                VALUES (?, ?)
                """,
                (user_id, session_string),
            )
        await self.conn.commit()

    async def remove_columns_ubotdb(self):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                CREATE TABLE new_ubotdb (
                    user_id INTEGER PRIMARY KEY,
                    session_string TEXT NOT NULL
                )
            """
            )
            await cursor.execute(
                """
                INSERT INTO new_ubotdb (user_id, session_string)
                SELECT user_id, session_string FROM ubotdb
            """
            )
            await cursor.execute("DROP TABLE ubotdb")
            await cursor.execute("ALTER TABLE new_ubotdb RENAME TO ubotdb")
        await self.conn.commit()

    async def remove_ubot(self, user_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute("DELETE FROM ubotdb WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def get_ubot(self, user_id):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT user_id, session_string FROM ubotdb WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            if row:
                user_id, session_string = row
                return {
                    "name": str(user_id),
                    "session_string": session_string,
                }
            else:
                return None

    async def get_userbots(self):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT user_id, session_string FROM ubotdb WHERE user_id IS NOT NULL"
            )
            rows = await cursor.fetchall()
            return [
                {
                    "name": str(user_id),
                    "session_string": session_string,
                }
                for user_id, session_string in rows
            ]

    async def get_flood(self, gw: int, user_id: int):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT flood FROM floods WHERE gw = ? AND user_id = ?", (gw, user_id)
            )
            result = await cursor.fetchone()
            return result[0] if result else None

    async def set_flood(self, gw: int, user_id: int, flood: str):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO floods (gw, user_id, flood)
                VALUES (?, ?, ?)
            """,
                (gw, user_id, flood),
            )
        await self.conn.commit()

    async def remove_all_deleted_vars(self):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT _id FROM variabel")
            ids = await cursor.fetchall()
            for (_id,) in ids:
                await cursor.execute(
                    "UPDATE variabel SET vars = json_remove(vars, '$.vars.DELETED') WHERE _id = ?",
                    (_id,),
                )

        await self.conn.commit()
        self._invalidate()

    async def rem_flood(self, gw: int, user_id: int):
        await self.ensure_connection()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM floods WHERE gw = ? AND user_id = ?", (gw, user_id)
            )
        await self.conn.commit()

    async def backup_database(self):
        db_file = Path(self.db_path)
        env_file = Path(self.env_path)
        if not db_file.exists():
            print(f"⚠️ File {self.db_path} tidak ditemukan!")
            return None
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        temp_db_file = self.temp_dir / db_file.name
        if env_file.exists():
            await aioshutil.copy(env_file, temp_db_file)
            await aioshutil.copy(db_file, temp_db_file)
        else:
            await aioshutil.copy(db_file, temp_db_file)
        archive_full_path = await aioshutil.make_archive(
            self.db_backup, self.db_backup_format, self.temp_dir
        )
        await aioshutil.rmtree(self.temp_dir)
        print(f"✅ Arsip berhasil dibuat: {archive_full_path}")
        return archive_full_path

    async def close(self):
        if self.conn:
            await self.conn.close()
            print("Database connection closed.")


# Initialize database
dB = DatabaseClient()
