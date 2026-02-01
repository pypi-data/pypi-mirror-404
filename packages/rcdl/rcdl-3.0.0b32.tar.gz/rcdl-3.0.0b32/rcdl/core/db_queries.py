# core/db_queries.py
"""
Hold SQL STRING
"""

CREATE_MEDIAS_TABLE = """
CREATE TABLE IF NOT EXISTS medias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT,
    service TEXT,
    url TEXT,
    duration REAL,
    sequence INTEGER,
    status TEXT,
    checksum TEXT,
    file_path TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    file_size INTEGER,
    fail_count INTEGER,
    UNIQUE(post_id, url)
)
"""

CREATE_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    user TEXT,
    service TEXT,
    domain TEXT,
    published DATETIME,
    json_hash TEXT,
    raw_json JSON,
    fetched_at DATETIME
)
"""

CREATE_FUSE_TABLE = """
CREATE TABLE IF NOT EXISTS fuses (
    id TEXT PRIMARY KEY,
    duration INTEGER,
    total_parts INTEGER,
    status TEXT,
    checksum TEXT,
    file_path TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    file_size INTEGER,
    fail_count INTEGER
)
"""

INSERT_POST = """
INSERT OR IGNORE INTO posts (
    id, user, service, domain, published,
    json_hash, raw_json, fetched_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_FUSED_MEDIA = """
INSERT OR IGNORE INTO fuses (
    id, duration, total_parts, status, checksum,
    file_path, created_at, updated_at, file_size, fail_count
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_MEDIA = """
INSERT OR IGNORE INTO medias (
    post_id, service, url, duration, sequence, status,
    checksum, file_path, created_at, updated_at, file_size, fail_count
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_MEDIA = """
UPDATE medias
SET duration = ?, file_size = ?, checksum = ?, status = ?,
    created_at = ?, updated_at = ?, fail_count = ?
WHERE post_id = ? AND url = ?
"""

UPDATE_FUSE = """
UPDATE fuses
SET duration = ?, status = ?, checksum = ?,
    created_at = ?, updated_at = ?, file_size = ?,
    fail_count = ?
WHERE id = ?
"""

QUERY_POST_ID = "SELECT * FROM posts WHERE id = ?"
QUERY_POST_USER = "SELECT * FROM posts WHERE user = ?"
QUERY_MEDIA_STATUS = "SELECT * FROM medias WHERE status = ?"
QUERY_MEDIA_ID = "SELECT * FROM medias WHERE post_id = ?"
QUERY_MEDIA_ID_AND_FILEPATH = "SELECT * FROM medias WHERE post_id = ? AND file_path = ?"
QUERY_FUSES_STATUS = "SELECT * FROM fuses WHERE status = ?"
QUERY_FUSES_ID = "SELECT * FROM fuses WHERE id = ?"
