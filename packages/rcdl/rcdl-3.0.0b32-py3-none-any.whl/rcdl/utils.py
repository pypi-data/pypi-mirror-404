# utils.py

"""Hold collection of useful functions"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os
import time

from rcdl.core.config import Config
from rcdl.interface.ui import UI


def get_date_now() -> str:
    """Return an str of current datetime in isoformat"""
    return datetime.now(timezone.utc).isoformat()


def get_media_metadata(full_path: str) -> tuple[int, int, str]:
    """Get duration (if possible), file_size and checksum"""
    from rcdl.core.downloader_subprocess import ffprobe_get_duration

    path = Path(full_path)
    if not os.path.exists(path):
        UI.error(f"{path} path should exist but does not.")

    file_size = path.stat().st_size
    checksum = get_media_hash(path)
    if checksum is None:
        checksum = ""
    duration = ffprobe_get_duration(path)
    if duration is None:
        duration = 0
    return duration, file_size, checksum


def get_media_hash(path: Path, retries: int = Config.CHECKSUM_RETRY) -> str | None:
    """Return a hash of a video file"""
    for attempt in range(retries + 1):
        try:
            sha256_hash = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            checksum = sha256_hash.hexdigest()
            return checksum
        except OSError as e:
            if attempt >= retries:
                UI.error(
                    f"OSError: Failed to checksum {path} "
                    f"at attempt {attempt + 1} due to: {e}"
                )
                return None
            UI.warning(
                f"OSError: Failed to checksum {path} "
                f"at attempt {attempt + 1} due to: {e}"
            )
            time.sleep(1.0)


def get_json_hash(data: dict) -> tuple[str, str]:
    """Return a hash of a dict"""
    raw_json = json.dumps(data, sort_keys=True)
    json_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    return raw_json, json_hash


def bytes_to_mb(bytes: float | int) -> float:
    return bytes / (1024 * 1024)


def bytes_to_str(bytes: float | int) -> str:
    mb = bytes_to_mb(bytes)

    if mb > 1024:
        gb = mb / 1024
        return f"{gb:.1f} GB"
    return f"{mb:.1f} MB"


def clean_all(all: bool, partial: bool, cache: bool, medias_deleted: bool):
    """Remove partial file & external programm cache"""

    from rcdl.core.db import DB
    from rcdl.core.models import Status
    from rcdl.core.downloader_subprocess import ytdlp_clear_cache, kill_aria2c

    if all:
        partial = True
        cache = True
        medias_deleted = True

    # remove all partial file
    if partial:
        path = Config.BASE_DIR
        folders = os.listdir(path)

        for folder in folders:
            if folder.startswith("."):
                continue

            folder_full_path = os.path.join(path, folder)
            files = os.listdir(folder_full_path)

            for file in files:
                if (
                    file.endswith(".aria2")
                    or file.endswith(".part")
                    or file.endswith(".opti.mp4")
                ):
                    full_path = os.path.join(folder_full_path, file)
                    os.remove(full_path)
                    UI.info(f"Removed {full_path}")

    # cache
    if cache:
        # clear yt-dlp cache
        ytdlp_clear_cache()
        UI.info("Cleared yt-dlp cache dir")

        # kill aria2c
        kill_aria2c()
        UI.info("Kill aria2c")

    # medias with status deleted
    if medias_deleted:
        with DB() as db:
            medias = db.query_media_by_status(Status.TO_BE_DELETED)
        UI.info(f"Found {len(medias)} medias with DELETED status")

        if len(medias) == 0:
            return

        total_size = 0.0
        total_vid = 0
        for media in medias:
            with DB() as db:
                post = db.query_post_by_id(media.post_id)
            if post is None:
                UI.warning(f"Could not match post id {media.post_id} to a post")
                continue

            path = os.path.join(Config.creator_folder(post.user), media.file_path)
            if not os.path.exists:
                UI.error(f"Path {path} should exist. Does not")
                continue

            try:
                os.remove(path)
                UI.info(f"Removed '{path}' ({bytes_to_str(media.file_size)} MB)")
                total_size += media.file_size
                total_vid += 1
            except Exception as e:
                UI.error(f"Failed to rm media {media.post_id}/{media.url} due to: {e}")
                continue

            with DB() as db:
                media.status = Status.DELETED
                db.update_media(media)

        UI.info(f"Removed a total of {total_vid} videos {bytes_to_str(total_size)}")


def format_seconds(seconds: int | float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h}h:{m:02d}m:{s:02d}s"
    elif m > 0:
        return f"{m}m:{s:02d}s"
    else:
        return f"{s}s"
