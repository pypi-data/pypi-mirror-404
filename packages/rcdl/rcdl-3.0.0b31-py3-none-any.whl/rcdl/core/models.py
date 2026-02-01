# core/models.py

"""Hold all dataclass models and enums"""

from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    """Status for media"""

    PENDING = "pending"  # to be downloaded
    DOWNLOADED = "downloaded"  # video has been downloaded
    FUSED = "fused"  # video has been fused, and impliitly removed
    TO_BE_DELETED = "to_be_delete"  # video has been marked for delete
    DELETED = "deleted"  # video has been deleted
    OPTIMIZED = "optimized"  # video has been optimized (reduce file size)


class FusedStatus(Enum):
    """Status for fused group"""

    PENDING = "pending"
    FUSED = "fused"


class CreatorStatus(Enum):
    FAVORITED = "FAVORITED"
    NA = "NA"


@dataclass
class Post:
    """Post model that shadow post dict response of request
    Partially used in posts db (check db_queries.py)
    """

    id: str
    user: str
    service: str
    domain: str
    title: str
    substring: str
    published: str
    file: dict
    attachments: list
    json_hash: str
    raw_json: str
    fetched_at: str


@dataclass
class Media:
    """Media model: use in medias DB"""

    post_id: str
    service: str
    url: str
    duration: float
    sequence: int
    status: Status
    checksum: str
    file_path: str
    created_at: str
    updated_at: str
    file_size: int
    fail_count: int = 0


@dataclass
class FusedMedia:
    """Fuses group models.
    Used in fuses db."""

    id: str
    duration: int
    total_parts: int
    status: FusedStatus
    checksum: str
    file_path: str
    created_at: str
    updated_at: str
    file_size: int
    fail_count: int = 0


@dataclass
class Creator:
    """Creator model"""

    id: str
    name: str
    service: str
    domain: str
    indexed: str
    updated: str
    favorited: int

    status: CreatorStatus

    # param
    max_size: int
    max_posts: int
    min_date: str
    max_date: str
