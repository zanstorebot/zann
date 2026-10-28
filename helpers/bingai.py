import asyncio
import hashlib
import json
import os
import random
import re
from collections import OrderedDict
from typing import Dict, List, Optional

import aiofiles
import httpx

from logs import logger


class BingCookies:
    def __init__(self, cookies_file: str):
        self.cookies = self._load_cookies(cookies_file)
        self.shuffled_cookies = self.cookies.copy()
        random.shuffle(self.shuffled_cookies)
        self.current_index = 0

    def _load_cookies(self, cookies_file: str) -> List[Dict[str, str]]:
        with open(cookies_file, "r") as file:
            cookies_data = json.load(file)
        return cookies_data

    def get_next_cookie(self) -> Optional[Dict[str, str]]:
        if self.current_index >= len(self.shuffled_cookies):
            return None
        cookie = self.shuffled_cookies[self.current_index]
        self.current_index += 1
        return cookie

    def reset(self):
        self.shuffled_cookies = self.cookies.copy()
        random.shuffle(self.shuffled_cookies)
        self.current_index = 0


class AsyncImageGenerator:
    def __init__(self, auth_cookie_u: str, auth_cookie_srchhpgusr: str):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.bing.com/images/create",
            },
            cookies={"_U": auth_cookie_u, "SRCHHPGUSR": auth_cookie_srchhpgusr},
            timeout=httpx.Timeout(60.0),
        )

    async def generate(
        self, prompt: str, num_images: int, max_cycles: int = 4
    ) -> List[str]:
        images = []
        start_time = asyncio.get_event_loop().time()

        for cycle in range(1, max_cycles + 1):
            if len(images) >= num_images:
                break

            try:
                response = await self.client.post(
                    url=f"https://www.bing.com/images/create?q={prompt}&rt=3&FORM=GENCRE",
                    data={"q": prompt, "qs": "ds"},
                    follow_redirects=False,
                )
            except httpx.RequestError as e:
                logger.error(f"Request failed: {e}")
                break

            if response.status_code != 302:
                logger.error(f"Bing did not redirect, status: {response.status_code}")
                raise Exception("Request to Bing failed! (Redirect)")

            location = response.headers.get("Location")
            if not location:
                raise Exception("Redirect location not found")

            result_id = location.split("id=")[-1].split("&")[0]
            results_url = f"https://www.bing.com/images/create/async/results/{result_id}?q={prompt}"

            async for attempt in self._wait_for_results(results_url, timeout=200):
                new_images = [
                    "https://tse" + link.split("?w=")[0]
                    for link in re.findall('src="https://tse([^"]+)"', attempt)
                ]
                if new_images:
                    images.extend(new_images)
                    images = list(OrderedDict.fromkeys(images))
                    if len(images) >= num_images:
                        break

        logger.info(
            f"Generated {len(images)} unique images in {round(asyncio.get_event_loop().time() - start_time, 2)} seconds."
        )
        return images[:num_images]

    async def save(self, images: List[str], output_dir: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        hashes = set()

        for idx, image_url in enumerate(images, start=1):
            try:
                response = await self.client.get(image_url)
                response.raise_for_status()

                img_hash = hashlib.md5(response.content).hexdigest()
                if img_hash in hashes:
                    logger.info(f"Skipped duplicate image: {image_url}")
                    continue

                hashes.add(img_hash)
                filename = f"image_{idx}.jpeg"
                async with aiofiles.open(os.path.join(output_dir, filename), "wb") as f:
                    await f.write(response.content)

                logger.info(f"Saved image: {filename}")
            except Exception as e:
                logger.warning(f"Failed to save image {image_url}: {e}")

    async def _wait_for_results(self, url: str, timeout: int):
        elapsed_time = 0
        while elapsed_time < timeout:
            response = await self.client.get(url)
            if (
                response.status_code == 200
                and response.text
                and "errorMessage" not in response.text
            ):
                yield response.text
                return
            else:
                await asyncio.sleep(1)
                elapsed_time += 1
        raise TimeoutError(f"No results within {timeout} seconds.")
