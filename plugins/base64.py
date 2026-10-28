import base64

from helpers import CMD


@CMD.UBOT("encode|decode")
async def _(client, message):
    text = client.get_text(message)
    if not text:
        return await message.reply(f"**Please give text to {message.command[0]}**")
    if message.command[0] == "encode":
        byt = text.encode("ascii")
        et = base64.b64encode(byt)
        atc = et.decode("ascii")
        return await message.reply(
            f"**=>> Encoded Text :** `{text}`\n\n**=>> OUTPUT :**\n`{atc}`"
        )
    elif message.command[0] == "decode":
        try:
            byt = text.encode("ascii")
            et = base64.b64decode(byt)
            atc = et.decode("ascii")
            return await message.reply(
                f"**=>> Dencoded Text :** `{text}`\n\n**=>> OUTPUT :**\n`{atc}`"
            )
        except Exception as er:
            return await message.reply(f"**ERROR:** {str(er)}")
