import os
import re
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont
from pyrogram import emoji



class Sticker:
    font_repo = "https://github.com/alicedevscodes/font.git"
    font_path = "font/SFUIDisplay-Bold.ttf"
    supported_types = ["jpeg", "png", "webp"]

    async def dl_font():
        if os.path.exists("font"):
            return
        os.system(f"git clone {Sticker.font_repo}")
        return

    async def add_text_img(image_path, text):
        await Sticker.dl_font()
        font_size = 12
        stroke_width = 1
        bottom_margin = 30

        if not os.path.exists(Sticker.font_path):
            raise FileNotFoundError(
                "Font tidak ditemukan di folder storage."
            )

        if ";" in text:
            upper_text, lower_text = text.split(";")
        else:
            upper_text = text
            lower_text = ""

        img = Image.open(image_path).convert("RGBA")
        img_info = img.info
        image_width, image_height = img.size

        font = ImageFont.truetype(
            font=Sticker.font_path, size=int(image_height * font_size) // 100
        )

        draw = ImageDraw.Draw(img)

        char_bbox = draw.textbbox((0, 0), "A", font=font)
        char_width = char_bbox[2] - char_bbox[0]
        char_height = char_bbox[3] - char_bbox[1]
        chars_per_line = image_width // char_width

        top_lines = textwrap.wrap(upper_text, width=chars_per_line)
        bottom_lines = textwrap.wrap(lower_text, width=chars_per_line)

        if top_lines:
            y = 10
            for line in top_lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                x = (image_width - line_width) / 2

                draw.text(
                    (x, y),
                    line,
                    fill="white",
                    font=font,
                    stroke_width=stroke_width,
                    stroke_fill="black",
                )

                y += line_bbox[3] - line_bbox[1]

        if bottom_lines:
            y = image_height - char_height * len(bottom_lines) - (bottom_margin + 50)
            for line in bottom_lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                x = (image_width - line_width) / 2

                draw.text(
                    (x, y),
                    line,
                    fill="white",
                    font=font,
                    stroke_width=stroke_width,
                    stroke_fill="black",
                )

                y += line_bbox[3] - line_bbox[1]

        final_image = os.path.join("memify.webp")
        img.save(final_image, **img_info)
        return final_image

  
    async def add_text_to_video(video_path, text):
        output_path = "output_sticker_with_text.webm"

        if ";" in text:
            upper_text, lower_text = text.split(";")
        else:
            upper_text = text
            lower_text = ""

        command = [
            "ffmpeg",
            "-i",
            video_path,
            "-vf",
            f"drawtext=text='{upper_text}':x=(w-text_w)/2:y=10:fontsize=40:fontcolor=white:borderw=2:bordercolor=black, "
            f"drawtext=text='{lower_text}':x=(w-text_w)/2:y=h-50:fontsize=40:fontcolor=white:borderw=2:bordercolor=black",
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "256k",
            "-an",
            "-y",
            output_path,
        ]

        subprocess.run(
            command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        return output_path

    def get_emoji_regex():
        e_list = [
            getattr(emoji, e).encode("unicode-escape").decode("ASCII")
            for e in dir(emoji)
            if not e.startswith("_")
        ]
        e_sort = sorted([x for x in e_list if not x.startswith("*")], reverse=True)
        pattern_ = f"({'|'.join(e_sort)})"
        return re.compile(pattern_)

    def resize_image(filename: str) -> str:
        im = Image.open(filename)
        maxsize = 512
        scale = maxsize / max(im.width, im.height)
        sizenew = (int(im.width * scale), int(im.height * scale))
        im = im.resize(sizenew, Image.NEAREST)
        downpath, f_name = os.path.split(filename)
        png_image = os.path.join(downpath, f"{f_name.split('.', 1)[0]}.png")
        im.save(png_image, "PNG")
        if png_image != filename:
            os.remove(filename)
        return png_image

    async def convert_video(filename: str) -> str:
        downpath, f_name = os.path.split(filename)
        webm_video = os.path.join(downpath, f"{f_name.split('.', 1)[0]}.webm")
        cmd = [
            "ffmpeg",  # <- Fix di sini
            "-loglevel",
            "quiet",
            "-i",
            filename,
            "-t",
            "00:00:03",
            "-vf",
            "fps=30",
            "-c:v",
            "vp9",
            "-b:v",
            "500k",
            "-preset",
            "ultrafast",
            "-s",
            "512x512",
            "-y",
            "-an",
            webm_video,
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if webm_video != filename:
            os.remove(filename)
        return webm_video
