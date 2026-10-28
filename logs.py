import logging
import os
import sys

import config


class ConnectionHandler(logging.Handler):
    def emit(self, record):
        for X in ["OSErro", "TimeoutError", "socket"]:
            if X in record.getMessage():
                args = sys.argv if sys.argv else ["src.py"]
                os.execl(sys.executable, sys.executable, *args)


logging.basicConfig(level=logging.INFO, format="%(name)s[%(levelname)s]: %(message)s")
connection_handler = ConnectionHandler()

for lib in {
    "pyrogram",
    "gunicorn",
    "flask",
    "pytgcalls",
    "aiorun",
    "asyncio",
    "hydrogram",
}:
    logging.getLogger(lib).setLevel(logging.ERROR)
    logging.getLogger(lib).addHandler(connection_handler)

logger = logging.getLogger(f"{config.BOT_NAME}")
