# core/opti.py

"""
Optimize media to reduce disk storage utilisation
"""

import os

from rcdl.core.config import Config
from rcdl.core.models import Status, Media
from rcdl.core.db import DB
from rcdl.core.downloader_subprocess import handbrake_optimized
from rcdl.interface.ui import UI, NestedProgress
from rcdl.utils import get_media_metadata, get_date_now


def update_db(media: Media, user: str, result: int):
    """Update DB if optimisation succesfful with new file_size, etc..."""
    if result == 0:
        path = os.path.join(Config.creator_folder(user), media.file_path)
        _, file_size, checksum = get_media_metadata(path)
        media.status = Status.OPTIMIZED
        media.checksum = checksum
        media.created_at = get_date_now()
        media.file_size = file_size

        with DB() as db:
            db.update_media(media)


def optimize():
    """Optimize all medias in DB with DOWNLOADED
    status that are not part of a fuse group"""
    # get all video to opti
    with DB() as db:
        medias = db.query_media_by_status(Status.DOWNLOADED)
        if Config.DEBUG:
            medias.extend(db.query_media_by_status(Status.OPTIMIZED))

    # progress
    progress = NestedProgress(UI.console)
    progress.start(
        total=len(medias),
        total_label="Optimizing videos",
        current_label="Current video",
    )

    for media in medias:
        # check media is not in a fuse group
        with DB() as db:
            fuse = db.query_fuses_by_id(media.post_id)
        if fuse is not None:
            progress.advance_total()
            continue

        # get post info
        with DB() as db:
            post = db.query_post_by_id(media.post_id)
        if post is None:
            UI.error(f"Could not match media {media.post_id} to a post by id")
            progress.advance_total()
            continue

        result = handbrake_optimized(media, post.user, progress)

        folder_path = Config.creator_folder(post.user)
        video_path = os.path.join(folder_path, media.file_path)
        output_path = video_path + ".opti.mp4"

        if result == 0:
            try:
                os.replace(output_path, video_path)
                update_db(media, post.user, result)
            except FileNotFoundError as e:
                UI.error(
                    f"FileNotFoundError: Could not replace {video_path} "
                    f"with {output_path} due to: {e}"
                )
            except PermissionError as e:
                UI.error(
                    f"PermissionError: Could not replace {video_path} "
                    f"with {output_path} due to: {e}"
                )
            except OSError as e:
                UI.error(
                    f"OSError: Failed to replace {video_path} with {output_path} due to: {e}"
                )
            finally:
                progress.advance_total()
    progress.close()
