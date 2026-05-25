# SECURE yt.py
# Original structure preserved
# API SYSTEM + YTPROXY KEPT
# Security hardened version

import asyncio
import glob
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Union

import requests
import yt_dlp

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from youtubesearchpython.__future__ import VideosSearch, CustomSearch

from AnnieXMedia import LOGGER
from AnnieXMedia.utils.database import is_on_off
from AnnieXMedia.utils.formatters import time_to_seconds

from config import YT_API_KEY, YTPROXY_URL as YTPROXY

logger = LOGGER(__name__)

os.umask(0o077)

DOWNLOAD_DIR = "downloads"
COOKIE_DIR = "cookies"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(COOKIE_DIR, exist_ok=True)

ALLOWED_COOKIES = [
    "cookies.txt",
    "youtube.txt",
]

SAFE_PROXY_DOMAINS = [
    "yourdomain.com",
    "api.yourdomain.com",
]


def safe_filename(name):
    return "".join(
        c for c in name
        if c.isalnum() or c in (" ", "_", "-")
    ).rstrip()


def is_safe_proxy(url):
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname
        return host in SAFE_PROXY_DOMAINS
    except Exception:
        return False


def cookie_txt_file():
    try:
        txt_files = [
            os.path.join(COOKIE_DIR, f)
            for f in ALLOWED_COOKIES
            if os.path.exists(os.path.join(COOKIE_DIR, f))
        ]

        if not txt_files:
            return None

        return random.choice(txt_files)

    except Exception:
        return None


async def check_file_size(link):

    async def get_format_info(link):

        args = [
            "yt-dlp",
            "-J",
            link,
        ]

        cookie = cookie_txt_file()

        if cookie:
            args.insert(1, "--cookies")
            args.insert(2, cookie)

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return None

        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0

        for fmt in formats:
            if fmt.get("filesize"):
                total_size += fmt["filesize"]

        return total_size

    info = await get_format_info(link)

    if info is None:
        return None

    formats = info.get("formats", [])

    if not formats:
        return None

    return parse_size(formats)


async def shell_cmd(cmd):

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    out, errorz = await proc.communicate()

    if errorz:
        err = errorz.decode("utf-8")

        if "unavailable videos are hidden" in err.lower():
            return out.decode("utf-8")

        return err

    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        )

        self.dl_stats = {
            "total_requests": 0,
            "okflix_downloads": 0,
            "cookie_downloads": 0,
            "existing_files": 0
        }

    async def exists(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        return bool(re.search(self.regex, link))

    async def url(
        self,
        message_1: Message
    ) -> Union[str, None]:

        messages = [message_1]

        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        text = ""
        offset = None
        length = None

        for message in messages:

            if offset:
                break

            if message.entities:

                for entity in message.entities:

                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset = entity.offset
                        length = entity.length
                        break

            elif message.caption_entities:

                for entity in message.caption_entities:

                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url

        if offset is None:
            return None

        return text[offset: offset + length]

    async def details(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        link = link.split("&")[0]
        link = link.split("?si=")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            title = result["title"]
            duration_min = result["duration"]

            thumbnail = (
                result["thumbnails"][0]["url"]
                .split("?")[0]
            )

            vidid = result["id"]

            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(
                    time_to_seconds(duration_min)
                )

        return (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        )

    async def title(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:
            return (
                result["thumbnails"][0]["url"]
                .split("?")[0]
            )

    async def track(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            track_details = {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0],
            }

            return track_details, result["id"]

    async def formats(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "cookiefile": cookie_txt_file(),
            "socket_timeout": 20,
            "max_filesize": 500 * 1024 * 1024,
        }

        formats_available = []

        try:

            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:

                r = ydl.extract_info(
                    link,
                    download=False
                )

                for fmt in r["formats"]:

                    try:
                        str(fmt["format"])
                    except Exception:
                        continue

                    if "dash" in str(
                        fmt["format"]
                    ).lower():
                        continue

                    try:

                        formats_available.append(
                            {
                                "format": fmt["format"],
                                "filesize": fmt.get("filesize"),
                                "format_id": fmt["format_id"],
                                "ext": fmt["ext"],
                                "format_note": fmt.get("format_note"),
                                "yturl": link,
                            }
                        )

                    except Exception:
                        continue

        except Exception:
            logger.exception(
                "Formats extraction failed"
            )

        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        try:

            results = []

            search = VideosSearch(
                link,
                limit=10
            )

            search_results = (
                await search.next()
            ).get("result", [])

            for result in search_results:

                duration_str = result.get(
                    "duration",
                    "0:00"
                )

                try:

                    parts = duration_str.split(":")

                    duration_secs = 0

                    if len(parts) == 3:
                        duration_secs = (
                            int(parts[0]) * 3600
                            + int(parts[1]) * 60
                            + int(parts[2])
                        )

                    elif len(parts) == 2:
                        duration_secs = (
                            int(parts[0]) * 60
                            + int(parts[1])
                        )

                    if duration_secs <= 3600:
                        results.append(result)

                except Exception:
                    continue

            if (
                not results
                or query_type >= len(results)
            ):
                raise ValueError(
                    "No suitable videos found"
                )

            selected = results[query_type]

            return (
                selected["title"],
                selected["duration"],
                selected["thumbnails"][0]["url"].split("?")[0],
                selected["id"]
            )

        except Exception:
            logger.exception("Slider failed")
            raise ValueError(
                "Failed to fetch video details"
            )

    async def video(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        args = [
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link,
        ]

        cookie = cookie_txt_file()

        if cookie:
            args.insert(1, "--cookies")
            args.insert(2, cookie)

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if stdout:
            return 1, stdout.decode().split("\n")[0]

        return 0, stderr.decode()

    async def playlist(
        self,
        link,
        limit,
        user_id,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.listbase + link

        args = [
            "yt-dlp",
            "-i",
            "--get-id",
            "--flat-playlist",
            "--playlist-end",
            str(limit),
            "--skip-download",
            link,
        ]

        cookie = cookie_txt_file()

        if cookie:
            args.insert(1, "--cookies")
            args.insert(2, cookie)

        playlist = await shell_cmd(args)

        try:
            result = playlist.split("\n")
            result = [x for x in result if x]
        except Exception:
            result = []

        return result

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):

        if videoid:
            vid_id = link
            link = self.base + link

        safe_title = safe_filename(
            title or "download"
        )

        loop = asyncio.get_running_loop()

        def create_session():

            session = requests.Session()

            retries = Retry(
                total=3,
                backoff_factor=0.3
            )

            session.mount(
                "http://",
                HTTPAdapter(max_retries=retries)
            )

            session.mount(
                "https://",
                HTTPAdapter(max_retries=retries)
            )

            return session
