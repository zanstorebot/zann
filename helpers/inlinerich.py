from pyrogram import raw
from pyrogram.types import InputMessageContent


class InputRichMessageContent(InputMessageContent):
    def __init__(self, rich_message):
        super().__init__()
        self.rich_message = rich_message

    async def write(self, client, reply_markup):
        return raw.types.InputBotInlineMessageRichMessage(
            rich_message=self.rich_message.write(),
            reply_markup=await reply_markup.write(client) if reply_markup else None,
        )

class InlineRichProxy:
    """Membungkus client agar edit_rich_message mengedit pesan inline."""

    def __init__(self, client, inline_message_id):
        self._client = client
        self._inline_message_id = inline_message_id

    async def edit_rich_message(self, chat_id, message_id, rich_message, reply_markup=None):
        return await self._client.edit_inline_text(
            self._inline_message_id,
            rich_message=rich_message,
            reply_markup=reply_markup,
        )

    def __getattr__(self, name):
        return getattr(self._client, name)