async def cb_help(client, callback_query):
    await callback_query.answer()
    mod_match = re.match(r"help_module\((.+?),(.+?)\)", callback_query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", callback_query.data)
    next_match = re.match(r"help_next\((.+?)\)", callback_query.data)
    back_match = re.match(r"help_back\((\d+)\)", callback_query.data)
    create_match = re.match(r"help_create", callback_query.data)
    user_id = callback_query.from_user.id
    is_bot = await dB.get_var(user_id, "is_bot")
    is_bot_pro = await dB.get_var(user_id, "is_bot_pro")
    if is_bot:
        is_pro = True if is_bot_pro else False
    else:
        plan = await dB.get_var(user_id, "plan")
        is_pro = True if plan == "is_pro" else False
    visible_helpable = {
        name: data for name, data in HELPABLE.items() if is_pro or not data["is_pro"]
    }
    prefix = alice.get_prefix(user_id)
    x_ = next(iter(prefix))
    full = f"<a href=tg://user?id={callback_query.from_user.id}>{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}</a>"
    cekpic = await dB.get_var(user_id, "HELP_LOGO")
    text_help = (
        await dB.get_var(user_id, "text_help")
        or f"**🤖 {BOT_NAME} by {USENAME_OWNER}**"
    )
    text_help2 = f"<blockquote>**🤖 {BOT_NAME} by {USENAME_OWNER}**</blockquote>"
    costum_cq = (
        callback_query.edit_message_caption
        if cekpic
        else callback_query.edit_message_text
    )
    costum_text = "caption" if cekpic else "text"
    if mod_match:
        module_name = mod_match.group(1)
        logger.info(f"line 48: {module_name}")
        prev_page_num = int(mod_match.group(2))
        state.set(user_id, "prev_page_num", prev_page_num)
    
        module_obj = visible_helpable[module_name]["module"]
    
        if hasattr(module_obj, "__HELP_RICH__") and callback_query.message is not None:
            chat_id = callback_query.message.chat.id
            msg_id = callback_query.message.id
            try:
                await module_obj.__HELP_RICH__(
                    client, chat_id, x_, text_help2,
                    message_id=msg_id, prev_page_num=prev_page_num,
                )
                return
            except Exception as e:
                logger.info(f"rich gagal, pakai help biasa: {e}")

        bot_text = f"{module_obj.__HELP__}".format(x_, text_help2)
          