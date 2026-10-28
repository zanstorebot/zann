from database import dB
from helpers import Emoji, animate_proses

from .autobc_command import extract_type_and_text


async def autoread_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if len(message.command) < 2:
        await proses.edit(f"{em.gagal}**Please type see help for module.**")
        return
    query, value = extract_type_and_text(message)
    if query.lower() == "time":
        if value.isnumeric():
            lmt = int(value)
            await dB.set_var(client.me.id, "TIME_READ", lmt)
            await proses.edit(f"{em.sukses}Time autoread set to: `{lmt}`")
            return
        else:
            await proses.edit(f"{em.gagal}Please give me seconds time!!")
            return
    elif query.lower() == "group":
        if value.lower() == "on":
            await dB.set_var(client.me.id, "READ_GC", True)
            await proses.edit(f"{em.sukses}**Successfully turned on group autoread.**")
            return
        elif value.lower() == "off":
            await dB.remove_var(client.me.id, "READ_GC")
            await proses.edit(
                f"{em.sukses}**Autoread {query} was successfully disabled.**"
            )
            return
        else:
            return await proses.edit(f"{em.gagal}**Please use value on or off!!**")
    elif query.lower() == "private":
        if value.lower() == "on":
            await dB.set_var(client.me.id, "READ_US", True)
            await proses.edit(f"{em.sukses}**Successfully turned on user autoread.**")
            return
        elif value.lower() == "off":
            await dB.remove_var(client.me.id, "READ_US")
            await proses.edit(
                f"{em.sukses}**Autoread {query} was successfully disabled.**"
            )
            return
        else:
            return await proses.edit(f"{em.gagal}**Please use value on or off!!**")
    elif query.lower() == "bot":
        if value.lower() == "on":
            await dB.set_var(client.me.id, "READ_BOT", True)
            await proses.edit(f"{em.sukses}**Successfully turned on autoread bot.**")
            return
        elif value.lower() == "off":
            await dB.remove_var(client.me.id, "READ_BOT")
            await proses.edit(
                f"{em.sukses}**Autoread {query} was successfully disabled.**"
            )
            return
        else:
            return await proses.edit(f"{em.gagal}**Please use value on or off!!**")
    elif query.lower() == "channel":
        if value.lower() == "on":
            await dB.set_var(client.me.id, "READ_CH", True)
            await proses.edit(
                f"{em.sukses}**Successfully turned on autoread channel.**"
            )
            return
        elif value.lower() == "off":
            await dB.remove_var(client.me.id, "READ_CH")
            await proses.edit(
                f"{em.sukses}**Autoread {query} was successfully disabled.**"
            )
            return

        else:
            return await proses.edit(f"{em.gagal}**Please use value on or off!!**")
    elif query.lower() == "tag":
        if value.lower() == "on":
            await dB.set_var(client.me.id, "READ_MENTION", True)
            await proses.edit(f"{em.sukses}**Successfully turned on autoread mention.")
            return
        elif value.lower() == "off":
            await dB.remove_var(client.me.id, "READ_MENTION")
            await proses.edit(
                f"{em.sukses}**Autoread {query} was successfully disabled.**"
            )
            return
        else:
            return await proses.edit(f"{em.gagal}**Please use value on or off!!**")
    elif query.lower() == "all":
        if value.lower() == "on":
            await dB.set_var(client.me.id, "READ_ALL", True)
            await proses.edit(f"{em.sukses}**Successfully turned on autoread all.**")
            return
        elif value.lower() == "off":
            await dB.remove_var(client.me.id, "READ_ALL")
            await proses.edit(
                f"{em.sukses}**Autoread {query} was successfully disabled.**"
            )
            return
        else:
            return await proses.edit(f"{em.gagal}**Please use value on or off!!**")
    elif query.lower() == "status":
        time_read = await dB.get_var(client.me.id, "TIME_READ") or 3600
        read_gc = (
            f"{em.sukses}**On**"
            if await dB.get_var(client.me.id, "READ_GC")
            else f"{em.gagal}**Off**"
        )
        read_us = (
            f"{em.sukses}**On**"
            if await dB.get_var(client.me.id, "READ_US")
            else f"{em.gagal}**Off**"
        )
        read_bot = (
            f"{em.sukses}**On**"
            if await dB.get_var(client.me.id, "READ_BOT")
            else f"{em.gagal}**Off**"
        )
        read_ch = (
            f"{em.sukses}**On**"
            if await dB.get_var(client.me.id, "READ_CH")
            else f"{em.gagal}**Off**"
        )
        read_tag = (
            f"{em.sukses}**On**"
            if await dB.get_var(client.me.id, "READ_MENTION")
            else f"{em.gagal}**Off**"
        )
        read_all = (
            f"{em.sukses}**On**"
            if await dB.get_var(client.me.id, "READ_ALL")
            else f"{em.gagal}**Off**"
        )

        status_text = (
            f"{em.proses}**Autoread Status**\n\n"
            f"{em.uptime}**Time Read: `{time_read}` seconds**\n"
            f"{em.profil}**Group:** {read_gc}\n"
            f"{em.msg}**Private:** {read_us}\n"
            f"{em.robot}**Bot:** {read_bot}\n"
            f"{em.klip}**Channel:** {read_ch}\n"
            f"{em.owner}**Mention:** {read_tag}\n"
            f"{em.speed}**All:** {read_all}"
        )
        await proses.edit(status_text)
        return

    else:
        await proses.edit(f"{em.gagal}**Please enter the query correctly!!**")
        return
