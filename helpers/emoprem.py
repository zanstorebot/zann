from pyrogram.types import RichTextCustomEmoji


def emo(emoji_id, alt="✨", custom=True):
    """Emoji premium untuk rich message.
    custom=False -> pakai emoji biasa (untuk edit di grup / pesan inline)."""
    if not custom:
        return alt
    return RichTextCustomEmoji(custom_emoji_id=str(emoji_id), alternative_text=alt)