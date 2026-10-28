import asyncio
import json
import os
import random
import string
from datetime import datetime
from typing import Dict, Optional, Tuple

import aiofiles


class TokenReferal:
    def __init__(self, database_file=f"token.json"):
        self.database_file = database_file
        self.users = {}
        self.referrals = {}
        self.tokens = {}
        self.lock = asyncio.Lock()

    async def load_database(self):
        if os.path.exists(self.database_file):
            try:
                async with aiofiles.open(self.database_file, "r") as f:
                    content = await f.read()
                    if not content.strip():
                        # Kosong, isi default
                        self.users = {}
                        self.referrals = {}
                        self.tokens = {}
                        return
                    data = json.loads(content)
                    self.users = data.get("users", {})
                    self.referrals = data.get("referrals", {})
                    self.tokens = data.get("tokens", {})
            except Exception as e:
                print(f"Error loading database: {e}")

    async def save_database(self):
        data = {"users": self.users, "referrals": self.referrals, "tokens": self.tokens}
        async with aiofiles.open(self.database_file, "w") as f:
            await f.write(json.dumps(data, indent=4))

    @classmethod
    async def create(cls, database_file="token.json"):
        self = cls(database_file)
        await self.load_database()
        return self

    async def generate_token(
        self, length=16, group_size=4, separator="-", user_id=None
    ) -> str:
        characters = string.ascii_uppercase + string.digits
        raw_token = "".join(random.choice(characters) for _ in range(length))
        grouped_token = ""
        for i in range(0, length, group_size):
            grouped_token += raw_token[i : i + group_size]
            if i + group_size < length:
                grouped_token += separator
        clean_token = grouped_token.replace(separator, "")
        self.tokens[clean_token] = {
            "owner": user_id,
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "max_usage": 3,
            "usage_history": [],
        }

        async with self.lock:
            await self.save_database()

        return grouped_token

    async def generate_referral_code(self, user_id: str, length=6) -> str:
        user_id = str(user_id)
        prefix = "ALICE-"
        characters = string.ascii_uppercase + string.digits
        code = "".join(random.choice(characters) for _ in range(length))
        referral_code = prefix + code

        for code, data in list(self.referrals.items()):
            if data.get("owner") == user_id:
                del self.referrals[code]
                break  # diasumsikan satu referral per user

        self.referrals[referral_code] = {
            "owner": user_id,
            "created_at": datetime.now().isoformat(),
            "invited_users": [],
        }

        if user_id not in self.users:
            self.users[user_id] = {}

        self.users[user_id]["referral_code"] = referral_code
        self.users[user_id]["invited_users"] = []
        self.users[user_id]["created_at"] = datetime.now().isoformat()

        async with self.lock:
            await self.save_database()
        return referral_code

    async def register_user(
        self,
        user_id: str,
        phone: str = None,
        referral_code: str = None,
    ) -> Dict:
        user_id = str(user_id)
        token = await self.generate_token(user_id=user_id)
        user_data = {
            "user_id": user_id,
            "phone": phone,
            "token": token,
            "registered_at": datetime.now().isoformat(),
            "referred_by": None,
            "referral_code": None,
            "invited_users": [],
        }
        if referral_code and referral_code in self.referrals:
            referrer = self.referrals[referral_code]["owner"]
            user_data["referred_by"] = referrer
            self.referrals[referral_code]["invited_users"].append(user_id)
            if referrer in self.users:
                self.users[referrer]["invited_users"].append(user_id)
        user_referral_code = await self.generate_referral_code(user_id)
        user_data["referral_code"] = user_referral_code
        self.users[user_id] = user_data
        async with self.lock:
            await self.save_database()

        return user_data

    async def check_token_usage(self, token: str) -> Dict:
        clean_token = token.replace("-", "")
        if clean_token not in self.tokens:
            return {
                "valid": False,
                "message": "Token tidak valid",
                "usage_count": 0,
                "max_usage": 3,
                "remaining_usage": 0,
            }

        token_data = self.tokens[clean_token]
        usage_count = token_data["usage_count"]
        max_usage = token_data["max_usage"]
        remaining_usage = max_usage - usage_count

        return {
            "valid": True,
            "message": "Token valid",
            "usage_count": usage_count,
            "max_usage": max_usage,
            "remaining_usage": remaining_usage,
            "owner": token_data["owner"],
            "created_at": token_data["created_at"],
            "usage_history": token_data["usage_history"],
        }

    async def verify_token(self, token: str) -> Optional[Dict]:
        clean_token = token.replace("-", "")
        if clean_token in self.tokens:
            token_data = self.tokens[clean_token]
            if token_data["usage_count"] >= token_data["max_usage"]:
                return None  # Token sudah melebihi batas penggunaan
            for user_id, user_data in self.users.items():
                if user_data.get("token").replace("-", "") == clean_token:
                    return user_data
        return None

    async def use_token(
        self, token: str, usage_description: str = "Token digunakan"
    ) -> Tuple[bool, str]:
        clean_token = token.replace("-", "")
        if clean_token not in self.tokens:
            return False, "Token tidak valid"
        token_data = self.tokens[clean_token]
        if token_data["usage_count"] >= token_data["max_usage"]:
            return (
                False,
                f"Token telah mencapai batas penggunaan maksimal ({token_data['max_usage']} kali)",
            )
        token_data["usage_count"] += 1
        token_data["usage_history"].append(
            {"timestamp": datetime.now().isoformat(), "description": usage_description}
        )
        async with self.lock:
            await self.save_database()
        remaining = token_data["max_usage"] - token_data["usage_count"]
        return True, f"Token berhasil digunakan. Sisa penggunaan: {remaining} kali"

    async def transfer_account(
        self, token: str, new_user_id: str, new_phone: str = None
    ) -> Tuple[bool, str]:
        user_data = await self.verify_token(token)
        if not user_data:
            return False, "Token tidak valid atau telah mencapai batas penggunaan"

        success, message = await self.use_token(
            token, f"Transfer akun ke {new_user_id}"
        )
        if not success:
            return False, message

        old_user_id = user_data["user_id"]
        new_user_id = str(new_user_id)

        if old_user_id == new_user_id:
            if new_phone:
                self.users[old_user_id]["phone"] = new_phone
                async with self.lock:
                    await self.save_database()
            return True, "Data pengguna diperbarui"

        old_token = user_data["token"]
        new_user_data = self.users.get(old_user_id, {}).copy()
        new_user_data["user_id"] = new_user_id
        new_user_data["owner"] = new_user_id
        new_user_data["token"] = old_token
        new_user_data["transferred_from"] = old_user_id
        new_user_data["transfer_date"] = datetime.now().isoformat()
        if new_phone:
            new_user_data["phone"] = new_phone

        self.users[new_user_id] = new_user_data
        self.users[old_user_id]["transferred_to"] = new_user_id
        self.users[old_user_id]["transfer_date"] = datetime.now().isoformat()

        for code, ref_data in list(self.referrals.items()):
            if ref_data["owner"] == old_user_id:
                ref_data["owner"] = new_user_id
                self.referrals[code] = ref_data
                self.users[new_user_id]["referral_code"] = code
                self.users[new_user_id]["invited_users"] = ref_data.get(
                    "invited_users", []
                )

        for token_key, token_data in self.tokens.items():
            if (
                token_data.get("user_id") == old_user_id
                or token_data.get("owner") == old_user_id
            ):
                self.tokens[token_key]["owner"] = new_user_id

        await self.delete_user_data(old_user_id)
        async with self.lock:
            await self.save_database()

        token_usage = await self.check_token_usage(old_token)
        ref_code = self.users[new_user_id].get("referral_code", "Tidak ada")
        return (
            True,
            f"Akun berhasil ditransfer.\n"
            f"🔑 Token: <code>{old_token}</code> (tersisa {token_usage['remaining_usage']} penggunaan)\n"
            f"🏷️ Referral code: <code>{ref_code}</code>",
        )

    async def reset_token_usage(self, token: str, admin_key: str) -> Tuple[bool, str]:
        if admin_key != "admin_secret_key":  # Ganti dengan kunci yang lebih aman
            return False, "Kunci admin tidak valid"
        clean_token = token.replace("-", "")
        if clean_token not in self.tokens:
            return False, "Token tidak valid"
        self.tokens[clean_token]["usage_count"] = 0
        self.tokens[clean_token]["usage_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "description": "Reset penggunaan oleh admin",
            }
        )
        async with self.lock:
            await self.save_database()
        return True, "Penggunaan token berhasil direset"

    async def revoke_token(self, user_id: str) -> Tuple[bool, str]:
        user_id = str(user_id)
        if user_id not in self.users:
            return False, "Pengguna tidak ditemukan"

        old_token = self.users[user_id].get("token", "")
        plain_old_token = old_token.replace("-", "") if old_token else None

        old_data = self.tokens.get(plain_old_token, {}) or self.tokens.get(
            old_token, {}
        )

        usage_count = old_data.get("usage_count", 0)
        max_usage = old_data.get("max_usage", 3)
        usage_history = old_data.get("usage_history", [])
        remaining_usage = max_usage - usage_count
        self.tokens.pop(plain_old_token, None)
        self.tokens.pop(old_token, None)
        length = 16
        group_size = 4
        separator = "-"
        characters = string.ascii_uppercase + string.digits
        raw_token = "".join(random.choice(characters) for _ in range(length))
        grouped_token = separator.join(
            raw_token[i : i + group_size] for i in range(0, length, group_size)
        )
        self.users[user_id]["token"] = grouped_token
        self.users[user_id]["token_revoked_at"] = datetime.now().isoformat()
        self.tokens[raw_token] = {
            "user_id": user_id,
            "owner": user_id,
            "created_at": datetime.now().isoformat(),
            "usage_count": usage_count,
            "max_usage": max_usage,
            "usage_history": usage_history,
            "remaining_usage": remaining_usage,
        }

        async with self.lock:
            await self.save_database()

        return (
            True,
            f"Token berhasil di-revoke dan diganti. Token baru: {grouped_token} dengan sisa penggunaan: {remaining_usage}",
        )

    async def get_referral_stats(self, user_id: str) -> Dict:
        if user_id not in self.users:
            return {"error": "Pengguna tidak ditemukan"}

        user = self.users[user_id]
        referral_code = user.get("referral_code")
        invited_count = len(user.get("invited_users", []))
        referred_by = user.get("referred_by", "-")
        token = user.get("token")

        if token and isinstance(token, str) and token.strip():
            token_usage = await self.check_token_usage(token)
        else:
            token_usage = {"remaining_usage": "-", "used": 0, "max_usage": "-"}

        stats = {
            "user_id": user_id,
            "referral_code": referral_code,
            "invited_users_count": invited_count,
            "invited_users": user.get("invited_users", []),
            "referred_by": referred_by,
            "token": token if token else "-",
            "token_usage": token_usage,
        }

        return stats

    async def delete_user_data(self, user_id: str) -> bool:
        user_id = str(user_id)
        found = False
        if user_id in self.users:
            del self.users[user_id]
            found = True
        for code, data in list(self.referrals.items()):
            if data.get("owner") == user_id:
                del self.referrals[code]
                found = True
        if hasattr(self, "tokens") and user_id in self.tokens:
            del self.tokens[user_id]
            found = True
        for ref_data in self.referrals.values():
            if "invited_users" in ref_data and user_id in ref_data["invited_users"]:
                ref_data["invited_users"].remove(user_id)
                found = True

        if found:
            async with self.lock:
                await self.save_database()
        return found
