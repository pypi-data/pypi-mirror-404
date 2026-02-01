# core/adapters.py

"""Convert [Any] into proper Models from models.py"""

import json
import sqlite3
from dataclasses import fields

from rcdl.core import parser
from rcdl.interface.ui import UI
from rcdl.core.models import Post, Media, Status, FusedMedia
from rcdl.utils import get_date_now, get_json_hash

VALID_POST_KEYS = set(
    [
        "id",
        "user",
        "service",
        "title",
        "substring",
        "published",
        "file",
        "attachments",
    ]
)


def _compute_json_metadata(raw: dict) -> tuple[str, str, str]:
    """From a json dict, return:
    - raw_json: str
    - json_hash: str
    - fetched_at str (datetime)
    """
    raw_json, json_hash = get_json_hash(raw)
    fetched_at = get_date_now()
    return raw_json, json_hash, fetched_at


def json_posts_to_posts(posts: list[dict]) -> list[Post]:
    """Convert a list of json post (dict) into a list of Post model
    Ignore if conversion failed"""
    formatted_posts = []
    for post in posts:
        p = json_post_to_post(post)
        if p is not None:
            formatted_posts.append(p)
    return formatted_posts


def json_post_to_post(post: dict) -> Post | None:
    """Convert a json post (dict) into a Post model
    or return None if covnersion failed"""
    post_keys = set(post)
    if post_keys != VALID_POST_KEYS:
        UI.error(
            f"Post id {post.get('id')} of {post.get('user')} "
            f"has invalid schema. "
            f"Missing: {VALID_POST_KEYS - post_keys}, "
            f"Extra: {post_keys - VALID_POST_KEYS}"
        )
        return None

    try:
        domain = parser.get_domain(post["service"])
        raw_json, json_hash, fetched_at = _compute_json_metadata(post)
        return Post(
            **post,
            domain=domain,
            json_hash=json_hash,
            raw_json=raw_json,
            fetched_at=fetched_at,
        )
    except TypeError as e:
        UI.error(
            f"Post id {post.get('id')} from {post.get('user')} could not be parsed: {e}"
        )
        return None


def row_to_post(row: sqlite3.Row) -> Post | None:
    """Convert a sqlite3 row into a Post model.
    Return None if conversion failed"""
    try:
        raw = json.loads(row["raw_json"])
        return Post(
            id=row["id"],
            user=row["user"],
            service=row["service"],
            domain=row["domain"],
            published=row["published"],
            json_hash=row["json_hash"],
            raw_json=row["raw_json"],
            fetched_at=row["fetched_at"],
            title=raw["title"],
            substring=raw["substring"],
            file=raw["file"],
            attachments=raw["attachments"],
        )
    except KeyError as e:
        UI.error(
            f"KeyError: Failed to convert {row['id']} (row_id) into Post model due to: {e}"
        )
        return None
    except TypeError as e:
        UI.error(
            f"TypeError: Failed to convert {row['id']} (row_id) into Post model due to: {e}"
        )
        return None
    except ValueError as e:
        UI.error(
            f"ValueError/JSONDecodeError: Failed to convert "
            f"{row['id']} (row_id) into Post model due to: {e}"
        )
        return None


def rows_to_posts(rows: list[sqlite3.Row]) -> list[Post]:
    """Convert a list of sqlite3 rows. Return a list of Post model.
    Ignore the row if conversion fail"""
    posts: list[Post] = []
    for row in rows:
        post = row_to_post(row)
        if post is not None:
            posts.append(post)

    if len(posts) != len(rows):
        UI.error(
            f"From {len(rows)} rows, only converted {len(posts)}."
            f" {len(rows) - len(posts)} error."
        )

    return posts


def row_to_media(row: sqlite3.Row) -> Media | None:
    """Convert a sqlite3 row into a Media model.
    Return None if conversion failed"""
    try:
        # create a dict to hold column of row that are present in Media.
        # Ignore column (like default autoincrement ID) that are not a field in Media
        media_data = {}
        for field in fields(Media):
            field_name = field.name
            if field_name in row.keys():
                value = row[field_name]
                if field_name == "status" and value is not None:
                    value = Status(value)
                media_data[field_name] = value
        return Media(**media_data)
    except (KeyError, TypeError, ValueError) as e:
        UI.error(
            f"Key/Type/Value Error: Failed to convert row {row['id']} into Post model due to {e}"
        )
        return None


def rows_to_medias(rows: list[sqlite3.Row]) -> list[Media]:
    """Convert a list of sqlite3 rows. Return a list of Media model.
    Ignore row if conversion failed"""
    medias: list[Media] = []
    for row in rows:
        media = row_to_media(row)
        if media is not None:
            medias.append(media)

    if len(medias) != len(rows):
        UI.error(
            f"From {len(rows)} rows, only converted {len(medias)}."
            f" {len(rows) - len(medias)} error."
        )

    return medias


def row_to_fused_media(row: sqlite3.Row) -> FusedMedia | None:
    """Convert a sqlite3 row into a FusedMedia model.
    Return None if conversion fail"""
    if row is None:
        return None
    try:
        fuses_data = {}
        for field in fields(FusedMedia):
            field_name = field.name
            if field_name in row.keys():
                value = row[field_name]
                if field_name == "status" and value is not None:
                    value = Status(value)
                fuses_data[field_name] = value
        return FusedMedia(**fuses_data)
    except (KeyError, TypeError, ValueError) as e:
        UI.error(
            f"Key/Type/Value Error: Failed to convert row "
            f"{row['id']} into FusedMedia model due to {e}"
        )
        return None


def rows_to_fuses(rows: list[sqlite3.Row]) -> list[FusedMedia]:
    """Convert a lsit of sqlite3 rows into a list of FusedMedia model
    Ignore row if conversion failed"""
    fuses: list[FusedMedia] = []
    for row in rows:
        fuse = row_to_fused_media(row)
        if fuse is not None:
            fuses.append(fuse)

    if len(fuses) != len(rows):
        UI.error(
            f"From {len(rows)} rows, only converted {len(fuses)}."
            f" {len(rows) - len(fuses)} error."
        )

    return fuses


def post_to_videos(post: Post) -> list[Media]:
    """Extract a list of Media model from a Post model"""
    json_post = json.loads(post.raw_json)

    urls = parser.extract_video_urls(json_post)
    sequence = 0
    medias: list[Media] = []
    for url in urls:
        medias.append(
            Media(
                post_id=post.id,
                service=post.service,
                url=url,
                duration=0.0,
                sequence=sequence,
                status=Status.PENDING,
                checksum="",
                file_path=parser.get_filename(json_post, url),
                created_at="",
                updated_at="",
                file_size=0,
                fail_count=0,
            )
        )
        sequence += 1
    return medias
