from command import inline_cmd
from helpers import CMD


@CMD.UBOT("alive")
async def _(client, message):
    return await inline_cmd(client, message)
