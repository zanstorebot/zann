import os

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyrogram.types import User


def download_image():
    if os.path.exists("storage/default.jpg"):
        return Image.open("storage/default.jpg").convert("RGBA").resize((140, 140))
    else:
        print("Error: File default.jpg tidak ditemukan.")
        return None


async def generate_profile_card(client, target):
    width, height = 800, 400
    bg_color = (30, 30, 40)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    frame_color = (50, 50, 70)
    draw.rounded_rectangle([(20, 20), (780, 380)], radius=30, fill=frame_color)

    profile_size = 140
    profile_x, profile_y = 60, 130
    profile_photo = None

    has_profile_photo = False
    profile_photo_path = f"downloads/profile_photo_{target.id}.jpg"

    is_private = isinstance(target, User)

    if is_private:
        first_name = target.first_name or "Pengguna"
        username_text = f"@{target.username}" if target.username else "Tidak ada"
        dc_id = getattr(target, "dc_id", "Tidak diketahui")
        is_premium = "Iya" if getattr(target, "is_premium", False) else "Tidak"

        details = [
            ("Nama", first_name),
            ("User ID", str(target.id)),
            ("Username", username_text),
            ("DC ID", str(dc_id)),
            ("Premium", is_premium),
        ]
    else:
        title = target.title or "Tidak diketahui"
        username_text = f"@{target.username}" if target.username else "Tidak ada"
        type_text = target.type.name.capitalize()
        members = getattr(target, "members_count", "Tidak diketahui")
        dc_id = getattr(target, "dc_id", "Tidak diketahui")
        details = [
            ("Nama", title),
            ("Chat ID", str(target.id)),
            ("Username", username_text),
            ("DC ID", str(dc_id)),
            ("Tipe", type_text),
            ("Total", f"{str(members)} Anggota"),
        ]

    async for photo in client.get_chat_photos(target.id, limit=1):
        await client.download_media(photo.file_id, file_name=profile_photo_path)
        has_profile_photo = True
        break

    if has_profile_photo and os.path.exists(profile_photo_path):
        profile_photo = (
            Image.open(profile_photo_path)
            .convert("RGBA")
            .resize((profile_size, profile_size))
        )
    else:
        profile_photo = download_image()

    if profile_photo:
        mask = Image.new("L", (profile_size, profile_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, profile_size, profile_size), fill=255)
        profile_photo = ImageOps.fit(profile_photo, (profile_size, profile_size))
        profile_photo.putalpha(mask)
        img.paste(profile_photo, (profile_x, profile_y), profile_photo)

    font_title = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36
    )
    font_text = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
    )

    draw.text((230, 40), "TELEGRAM ID CARD", font=font_title, fill=(255, 220, 100))

    label_color = (200, 200, 200)
    value_color = (173, 216, 230)
    y_text = 100
    for label, value in details:
        draw.text((230, y_text), f"{label}:", font=font_text, fill=label_color)
        draw.text((400, y_text), value, font=font_text, fill=value_color)
        y_text += 50

    save_dir = "./downloads"
    os.makedirs(save_dir, exist_ok=True)
    final_path = os.path.join(save_dir, f"profile_card_{target.id}.jpg")
    img.save(final_path, "JPEG")

    return final_path
