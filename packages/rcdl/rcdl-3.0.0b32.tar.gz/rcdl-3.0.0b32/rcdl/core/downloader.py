# core/downloader.py

"""
Handle post, media download to website
"""

import logging
import os
import json

import requests

from rcdl.interface.ui import UI, NestedProgress
from rcdl.core import parser
from rcdl.core import adapters
from rcdl.core.api import URL
from rcdl.core.config import Config
from rcdl.core.models import (
    Creator,
    Status,
    Media,
    Post,
    FusedMedia,
    FusedStatus,
)
from rcdl.core.db import DB
from rcdl.core.downloader_subprocess import ytdlp_subprocess
from rcdl.core.file_io import write_json, load_json
from rcdl.utils import get_date_now, get_media_metadata


class PostsFetcher:
    """
    Fetch posts from api. Save as JSON. Handle multiple pages requests
    """

    def __init__(
        self, url: str, json_path: str, max_page: int = Config.DEFAULT_MAX_PAGE
    ):
        self.url = url
        self.json_path = json_path

        self.page = 0
        self.max_page = max_page

        self.status = 200

    def _request_page(self, url: str) -> requests.Response:
        """Request a single page and return json dict"""
        logging.info("RequestEngine url %s", url)
        headers = URL.get_headers()
        response = requests.get(url, headers=headers, timeout=Config.TIMEOUT)
        if response.status_code != 200:
            logging.warning("Failed request %s: %s", url, response.status_code)
        return response

    def request(self, params: dict | None = None):
        """Request multiple page of an url"""
        if params is None:
            params = {}

        with UI.progress_posts_fetcher(self.max_page) as progress:
            task = progress.add_task("Fetching posts", total=self.max_page)

            while self.status == 200 and self.page < self.max_page:
                o = self.page * Config.POST_PER_PAGE
                params["o"] = o
                url = URL.add_params(self.url, params)

                try:
                    # Dry run: not request acutally made
                    if Config.DRY_RUN:
                        logging.debug(
                            "DRY-RUN posts fetcher %s -> %s", url, self.json_path
                        )
                        self.page += 1
                        continue

                    response = self._request_page(url)
                    self.status = response.status_code

                    # if the programm crash while doing requests,
                    # previous requests are still saved and not overwritten.
                    if self.page > 0:
                        json_data = list(load_json(self.json_path))
                    else:
                        json_data = []

                    # for discover command, response json is in a
                    # different format and contains 'posts'
                    if self.status == 200:
                        if "posts" in response.json():
                            json_data.extend(response.json()["posts"])
                        else:
                            json_data.extend(response.json())

                        write_json(self.json_path, json_data, mode="w")

                    progress.update(
                        task,
                        advance=1,
                        description=(
                            f"Fetched {len(json_data)}"
                            f" posts (page {self.page + 1}/{self.max_page})"
                        ),
                    )
                except requests.RequestException as e:
                    logging.error(
                        "Failed to request %s (page: %s) deu to: %s", url, self.page, e
                    )
                except json.JSONDecodeError as e:
                    logging.error(
                        "Failed to decode JSON response of request %s due to: %s",
                        url,
                        e,
                    )
                finally:
                    self.page += 1


class MediaDownloader:
    """Handle downloading a list of media and update DB status"""

    def __init__(self):
        pass

    def _build_url(self, domain: str, url: str):
        """Return full url"""
        return URL.get_url_from_file(domain, url)

    def _build_full_path(self, user: str, media_path: str):
        """Return full path"""
        return os.path.join(Config.creator_folder(user), media_path)

    def _media_exist(self, full_path: str):
        """Check a file exist"""
        return os.path.exists(full_path)

    def _update_db(self, result: int, media: Media, full_path: str):
        """Update db information"""

        # video failed to download
        if result != 0:
            media.fail_count += 1
        else:
            duration, file_size, checksum = get_media_metadata(full_path)
            media.duration = duration
            media.status = Status.DOWNLOADED
            media.checksum = checksum
            media.created_at = get_date_now()
            media.file_size = file_size

        with DB() as db:
            db.update_media(media)

    def download(self, medias: list[Media], max_fail_count: int | None = None):
        """Download all medias in media with PENDING stats"""
        # init progress bar
        progress = NestedProgress(UI.console)
        progress.start(
            total=len(medias),
            total_label="Downloading videos",
            current_label="Current video",
        )

        max_try = Config.MAX_FAIL_COUNT
        if max_fail_count is not None:
            max_try = max_fail_count
        for media in medias:
            progress.start_current("Downloading", total=2)
            if media.fail_count > max_try:
                UI.warning(
                    f"Video skipped due to too many failed download attempt ({media.fail_count})"
                )
                progress.advance_total()
                continue

            # match post info from db with post_id to get user/creator_id
            with DB() as db:
                post = db.query_post_by_id(media.post_id)
            if post is None:
                UI.error(f"Could not match media post_id {media.post_id} with a post")
                progress.advance_total()
                continue

            # build full url and full path
            url = self._build_url(post.domain, media.url)
            full_path = self._build_full_path(post.user, media.file_path)

            # update progress bar info (video in download info)
            progress.set_status(f"{post.user}@({post.service}) -> ", media.file_path)

            # check video does not already exist
            if self._media_exist(full_path):
                UI.warning(
                    f"Video {url} @ {full_path} already exists. Possible DB problem"
                )
                self._update_db(0, media, full_path)
                progress.advance_total()
                continue

            # dry run: no actual download, skippe rest of fn
            if Config.DRY_RUN:
                UI.debug(f"(dry-run) dl  {post.user}@{full_path} from {url}")
                progress.advance_total()
                continue

            result = ytdlp_subprocess(url, full_path)
            self._update_db(result, media, full_path)
            progress.advance_total()
        progress.close()


def fetch_posts_by_tag(tag: str, max_page: int = Config.DEFAULT_MAX_PAGE) -> dict:
    """Helper function to get all posts from a search results"""
    url = URL.get_posts_page_url_wo_param()
    path = Config.cache_file(tag)
    pf = PostsFetcher(url, str(path), max_page=max_page)
    pf.request(params={"tag": tag})

    return load_json(path)


def fetch_posts_by_creator(creator: Creator, max_fail_count: int | None = None) -> dict:
    """Helper function to get all posts from a creator"""
    url = URL.get_creator_post_wo_param(creator)
    path = Config.cache_file(f"{creator.id}_{creator.service}")
    if max_fail_count is not None:
        pf = PostsFetcher(url, str(path), max_page=max_fail_count)
    else:
        pf = PostsFetcher(url, str(path))
    pf.request()

    return load_json(path)


def get_fuses_from_post(posts: list[Post]) -> list[FusedMedia]:
    """Update data on fuses database table for video to be fused"""
    fuses: list[FusedMedia] = []
    for post in posts:
        json_post = json.loads(post.raw_json)
        total_parts = len(parser.extract_video_urls(json_post))
        if total_parts > 1:
            fuses.append(
                FusedMedia(
                    id=post.id,
                    duration=0,
                    total_parts=total_parts,
                    status=FusedStatus.PENDING,
                    checksum="",
                    file_path=parser.get_filename_fuse(post),
                    created_at="",
                    updated_at="",
                    file_size=0,
                    fail_count=0,
                )
            )
    return fuses


def refresh_creators_videos(max_fail_count: int | None = None):
    """
    For each creator:
        - get posts with videos & update posts DB
        - extract all medias & update medias DB
        - extract fuses group & update fuses DB
    """
    creators = parser.get_creators()
    for creator in creators:
        UI.info(f"Creator {creator.id} from {creator.service}")

        # request all posts by creator
        fetch_posts_by_creator(creator, max_fail_count=max_fail_count)

        # only keep posts with video url (mp4, m4v, ...)
        posts_with_videos = parser.filter_posts_with_videos_from_json(
            str(Config.cache_file(f"{creator.id}_{creator.service}"))
        )

        # convert all json dict into Post model
        posts = adapters.json_posts_to_posts(posts_with_videos)

        # insert posts in db
        with DB() as db:
            db.insert_posts(posts)

        # find all multiple part videos and update db
        fuses = get_fuses_from_post(posts)
        with DB() as db:
            db.insert_fused_media(fuses)

        # convert all posts into videos
        medias = []
        for post in posts:
            medias.extend(adapters.post_to_videos(post))

        # insert videos in db
        with DB() as db:
            db.insert_medias(medias)


def download_videos_to_be_dl(max_fail_count: int | None):
    """
    Download all media with PENDING status in DB
    """
    with DB() as db:
        medias = db.query_media_by_status(Status.PENDING)

    media_downloader = MediaDownloader()
    media_downloader.download(medias, max_fail_count=max_fail_count)
