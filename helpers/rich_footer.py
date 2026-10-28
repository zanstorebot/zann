from pyrogram.helpers import cell, table

from config import NAMA_CORE
from helpers.emoprem import emo


from pyrogram.helpers import cell, table

from config import NAMA_CORE


def footer_cell(custom=True):
    return cell(
        [f"{NAMA_CORE} ", emo(5456140674028019486, "⚡", custom)],
        align="center",
    )


def footer_table(custom=True):
    return table([[footer_cell(custom)]])