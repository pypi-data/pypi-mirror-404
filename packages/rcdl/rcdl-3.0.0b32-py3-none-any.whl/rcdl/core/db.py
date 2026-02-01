# core/db.py

"""
Handle SQL Database
"""

import sqlite3

from rcdl.core import adapters
from rcdl.core import db_queries as queries
from rcdl.core.config import Config
from rcdl.core.models import Post, Media, Status, FusedMedia, FusedStatus
from rcdl.utils import get_date_now

from rcdl.interface.ui import UI


class DB:
    """Handle all sqlite database command"""

    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def __enter__(self):
        """necessary to use with openDB()"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """necessary to use with openDB()"""
        self.close()

    def close(self):
        """Properly close database"""
        self.conn.close()

    def init_database(self):
        """Create tables (posts, fuses, medias) if they dont exist"""
        self.conn.execute(queries.CREATE_POSTS_TABLE)
        self.conn.execute(queries.CREATE_MEDIAS_TABLE)
        self.conn.execute(queries.CREATE_FUSE_TABLE)

        self.conn.commit()

    def get_nb_per_status(self):
        """Return an info dict per tables with number of entry per status
        info['tables1']['status1'] = X
        ...
        """
        info = {}
        info["medias"] = {}
        info["fuses"] = {}
        info["posts"] = 0
        for status in Status:
            info["medias"][status] = len(self.query_media_by_status(status))
        for status in FusedStatus:
            info["fuses"][status] = len(self.query_fuses_by_status(status))

        cur = self.conn.execute(("SELECT COUNT(*) AS count FROM posts"))
        row = cur.fetchone()
        info["posts"] = row["count"] if row else 0
        return info

    def query_post_by_id(self, _id: str) -> Post | None:
        """Get a post from his post id"""
        row = self.conn.execute(queries.QUERY_POST_ID, (_id,)).fetchone()

        UI.debug(f"{queries.QUERY_POST_ID} {_id} returned {row}")

        if row is None:
            return None

        return adapters.row_to_post(row)

    def query_post_by_user(self, user: str) -> list[Post]:
        """Get all posts of a user"""
        cur = self.conn.cursor()
        cur.execute(queries.QUERY_POST_USER, (user,))
        rows = cur.fetchall()

        UI.debug(f"{queries.QUERY_POST_USER} {user} returned {len(rows)} results")

        return adapters.rows_to_posts(rows)

    def query_media_by_status(self, status: Status) -> list[Media]:
        """Get all medias with specified status"""
        rows = self.conn.execute(queries.QUERY_MEDIA_STATUS, (status.value,)).fetchall()
        UI.debug(
            f"{queries.QUERY_MEDIA_STATUS} {status.value} returned {len(rows)} result"
        )

        return adapters.rows_to_medias(rows)

    def query_medias_by_status_sorted(
        self,
        status: Status | list[Status],
        sort_by: str | None = None,
        ascending: bool = True,
    ) -> list[Media]:
        """Get all medias with specified status (one or multiple)
        Return them sorted by column and asc or desc"""

        # validate sort column
        valid_columns = {
            "id",
            "post_id",
            "service",
            "url",
            "duration",
            "sequence",
            "status",
            "checksum",
            "file_path",
            "created_at",
            "updated_at",
            "file_size",
            "fail_count",
        }
        order_clause = ""
        if sort_by:
            if sort_by not in valid_columns:
                UI.error(f"Invalid sort column: {sort_by}")
            order_clause = f"ORDER BY {sort_by} {'ASC' if ascending else 'DESC'}"

        # status filter
        if isinstance(status, Status):
            status = [status]

        status_values = [s.value if isinstance(s, Status) else s for s in status]
        placeholders = ", ".join("?" for _ in status_values)

        sql = f"SELECT * FROM medias WHERE status IN ({placeholders}) {order_clause}"
        rows = self.conn.execute(sql, status_values).fetchall()

        UI.debug(
            f"Queried medias with status={status_values}, sorted by {sort_by}, ascending={ascending}, {len(rows)} results"
        )

        return adapters.rows_to_medias(rows)

    def query_media_by_post_id(self, _id: str) -> list[Media]:
        """Get all medias from the same post by post id"""
        rows = self.conn.execute(queries.QUERY_MEDIA_ID, (_id,)).fetchall()
        UI.debug(f"{queries.QUERY_MEDIA_ID} {_id} returned {len(rows)} result")
        return adapters.rows_to_medias(rows)

    def query_media_by_post_id_and_file_path(
        self, _id: str, file_path: str
    ) -> Media | None:
        """Get a media from its post id and file_path"""
        row = self.conn.execute(
            queries.QUERY_MEDIA_ID_AND_FILEPATH, (_id, file_path)
        ).fetchone()
        return adapters.row_to_media(row)

    def query_fuses_by_status(self, status: FusedStatus) -> list[FusedMedia]:
        """Get all fused_media with specified status"""
        rows = self.conn.execute(queries.QUERY_FUSES_STATUS, (status.value,)).fetchall()
        UI.debug(
            f"{queries.QUERY_FUSES_STATUS} {status.value} returned {len(rows)} result"
        )

        return adapters.rows_to_fuses(rows)

    def query_fuses_by_id(self, _id: str) -> FusedMedia | None:
        """Get a fuse group by its unique post id"""
        row = self.conn.execute(queries.QUERY_FUSES_ID, (_id,)).fetchone()
        UI.debug(f"{queries.QUERY_FUSES_ID} {_id} returned {row} result")
        return adapters.row_to_fused_media(row)

    def insert_posts(self, posts: list[Post] | Post):
        """Add post to DB if it does not already exist (UNIQUE post_id)"""
        if isinstance(posts, Post):
            posts = [posts]

        values = []
        for post in posts:
            values.append(
                (
                    post.id,
                    post.user,
                    post.service,
                    post.domain,
                    post.published,
                    post.json_hash,
                    post.raw_json,
                    post.fetched_at,
                )
            )

        with self.conn:
            self.conn.executemany(queries.INSERT_POST, values)

        inserted = self.conn.total_changes
        UI.debug(f"Inserted {inserted} new posts out of {len(posts)} total posts")

    def insert_medias(self, medias: list[Media] | Media):
        """Insert media into the db if it does not already exist (UNIQUE post_id, url)"""
        if isinstance(medias, Media):
            medias = [medias]

        values = []
        for media in medias:
            values.append(
                (
                    media.post_id,
                    media.service,
                    media.url,
                    media.duration,
                    media.sequence,
                    media.status.value,
                    media.checksum,
                    media.file_path,
                    media.created_at,
                    get_date_now(),
                    media.file_size,
                    media.fail_count,
                )
            )

        with self.conn:
            self.conn.executemany(queries.INSERT_MEDIA, values)

        inserted = self.conn.total_changes
        UI.debug(f"Inserted {inserted} new media out of {len(medias)} total medias")

    def update_media(self, media: Media):
        """Update media entry in the db. Found it by post_id & url, and update:
        - duration, file_size, checksum, status, create_at, updated_at, fail_count"""
        params = (
            media.duration,
            media.file_size,
            media.checksum,
            media.status.value,
            media.created_at,
            get_date_now(),
            media.fail_count,
            media.post_id,
            media.url,
        )
        with self.conn:
            self.conn.execute(queries.UPDATE_MEDIA, params)
            UI.debug(f"Updated media {media.post_id} / {media.url}")

    def insert_fused_media(self, fuses: list[FusedMedia] | FusedMedia):
        """Insert fused_media into the db if it does not already exist (UNIQUE post_id)"""
        if isinstance(fuses, FusedMedia):
            fuses = [fuses]

        values = []
        for fuse in fuses:
            values.append(
                (
                    fuse.id,
                    fuse.duration,
                    fuse.total_parts,
                    fuse.status.value,
                    fuse.checksum,
                    fuse.file_path,
                    fuse.created_at,
                    get_date_now(),
                    fuse.file_size,
                    fuse.fail_count,
                )
            )

        with self.conn:
            self.conn.executemany(queries.INSERT_FUSED_MEDIA, values)

        inserted = self.conn.total_changes
        UI.debug(
            f"Inserted {inserted} new fused_media out of {len(fuses)} total fused_media"
        )

    def update_fuse(self, fuse: FusedMedia):
        """Update fuse group: duration, status, checksum,
        created_at, updated_at, file_size, fail_count

        """
        params = (
            fuse.duration,
            fuse.status.value,
            fuse.checksum,
            fuse.created_at,
            get_date_now(),
            fuse.file_size,
            fuse.fail_count,
            fuse.id,
        )
        with self.conn:
            self.conn.execute(queries.UPDATE_FUSE, params)
            UI.debug(f"Updated fuse {fuse.id} / {fuse.file_path}")
