# core/parser.py

"""Handle function to parse post and files"""

import logging
from pathvalidate import sanitize_filename

from rcdl.interface.ui import UI
from rcdl.core.models import Media, Creator, Post, CreatorStatus
from rcdl.core.file_io import load_json, load_txt, write_txt
from rcdl.core.config import Config


COOMER_PAYSITES = ["onlyfans", "fansly", "candfans"]
KEMONO_PAYSITES = [
    "patreon",
    "fanbox",
    "fantia",
    "boosty",
    "gumroad",
    "subscribestar",
    "dlsite",
]


def get_domain(arg: str | dict | Media) -> str:
    """From a service get the domain (coomer or kemono)
    Input is either: service(str), post(dict), video(models.Video)
    """

    def _service(service: str) -> str:
        if service in COOMER_PAYSITES:
            return "coomer"
        if service in KEMONO_PAYSITES:
            return "kemono"
        logging.error("Service %s not associated to any domain", service)
        return ""

    if isinstance(arg, dict):
        return _service(arg["service"])
    if isinstance(arg, Media):
        return _service(arg.service)

    return _service(arg)


def get_title(post: Post) -> str:
    """From a Post Model return the title"""
    title = post.title
    if title == "":
        title = post.substring
    if title == "":
        title = post.id
    return sanitize_filename(title)


def get_title_json(post: dict) -> str:
    """Extract title from a post(dict)"""
    title = post["title"]
    if title == "":
        title = post["substring"]
    if title == "":
        title = post["id"]
    return sanitize_filename(title)


def get_date(post: dict) -> str:
    """Extract date from a post(dict)"""
    if "published" in post:
        date = post["published"][0:10]
    elif "added" in post:
        date = post["added"][0:10]
    else:
        logging.error("Could not extract date from %s", post["id"])
        date = "NA"
    return date


def get_part(post: dict, url: str) -> int:
    """
    For posts containing multiple video url. Each url is considered a part,
    so all videos from the same posts will simply have a different part number
    """
    urls = extract_video_urls(post)
    part = 0
    if len(urls) == 1:
        return 0

    for u in urls:
        if u == url:
            return part
        part += 1

    logging.error(
        "Could not extract part number for post id %s with url %s", post["id"], url
    )
    return -1


def get_filename(post: dict, url: str) -> str:
    """Get filename from pst dict and url"""
    title = get_title_json(post)
    date = get_date(post)
    part = get_part(post, url)
    file_title = f"{date}_{title}".replace("'", " ").replace('"', "")
    filename = f"{file_title}_p{part}.mp4"
    return filename


def get_filename_fuse(post: Post) -> str:
    """Get filename for fuse output from Post Model
    Fuse output has 'X' as part number"""
    title = get_title(post)
    date = post.published[0:10]
    part = "X"
    file_title = f"{date}_{title}".replace("'", " ").replace('"', "")
    filename = f"{file_title}_p{part}.mp4"
    return filename


def extract_video_urls(post: dict) -> list:
    """Extract all videos urls from a dict post"""
    video_extensions = (".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".m4v")
    urls = set()

    # Check main file
    if post["file"]:
        if post["file"]["path"]:
            path = post["file"]["path"]
            if path.endswith(video_extensions):
                urls.add(f"{path}")

    if post["attachments"]:
        attachments = post["attachments"]
        for attachment in attachments:
            if attachment["path"]:
                if attachment["path"].endswith(video_extensions):
                    urls.add(f"{attachment['path']}")

    return list(urls)


def filter_posts_with_videos_from_list(data: list[dict]) -> list[dict]:
    """Return posts with video url from a json with a list of posts"""

    posts_with_videos = []
    for post in data:
        if len(extract_video_urls(post)) > 0:
            posts_with_videos.append(post)
    return posts_with_videos


def filter_posts_with_videos_from_json(path: str) -> list:
    """Return posts with video url from a json with a list of posts"""
    posts = load_json(path)

    posts_with_videos = []
    for post in posts:
        if len(extract_video_urls(post)) > 0:
            posts_with_videos.append(post)
    return posts_with_videos


def valid_service(service: str) -> bool:
    """Check if a service is valid (within list of DOMAIN services)"""
    if service in COOMER_PAYSITES:
        return True
    if service in KEMONO_PAYSITES:
        return True
    return False


def _default_creator(_id: str, service: str, domain: str):
    return Creator(
        id=_id,
        service=service,
        domain=domain,
        name="",
        indexed="",
        updated="",
        favorited=1,
        status=CreatorStatus.NA,
        max_date="",
        max_posts=1,
        max_size=1,
        min_date="",
    )


def get_creator_from_line(line: str) -> Creator | None:
    """
    Convert a line into a Creator model
    arg: line -> 'service/creator'
    This is the format of creators.txt
    """

    parts = line.split("/")
    if valid_service(parts[0].strip()):
        return _default_creator(
            parts[1].strip(), parts[0].strip(), get_domain(parts[0].strip())
        )
    if valid_service(parts[1].strip()):
        return _default_creator(
            parts[0].strip(), parts[1].strip(), get_domain(parts[1].strip())
        )

    UI.error(
        f"Creator file not valid: {line} can not be interpreted."
        f" Format is: 'service/creator_id'"
    )
    return None


def get_creators() -> list[Creator]:
    """
    Load creators.txt and return a list of models.Creator
    """
    lines = load_txt(Config.CREATORS_FILE)
    creators = []
    for line in lines:
        creator = get_creator_from_line(line)
        if creator is None:
            continue
        creators.append(creator)
    if len(creators) < 1:
        UI.error(f"Could not find any creators. Check {Config.CREATORS_FILE}")
    return creators


def get_creators_from_posts(posts: list[dict]) -> list[Creator]:
    """Extract a list of Creators model form a list of dict posts"""
    creators = []
    seen = set()

    for post in posts:
        key = (post["user"], post["service"], "coomer")
        if key in seen:
            continue

        seen.add(key)
        creators.append(_default_creator(post["user"], post["service"], "coomer"))
    return creators


def parse_creator_input(value: str) -> tuple[str | None, str]:
    """Parse user input in cli to extract creator id & service"""
    value = value.strip()

    # url
    if "://" in value:
        parts = value.replace("https://", "").strip().split("/")
        logging.info(
            "From %s extracte service %s and creator %s", value, parts[1], parts[3]
        )
        return parts[1], parts[3]  # service, creator_id

    # creators.txt format
    if "/" in value:
        c = get_creator_from_line(value)
        if c is not None:
            logging.info(
                "From %s extracte service %s and creator %s",
                value,
                c.service,
                c.id,
            )
            return c.service, c.id

    logging.info("From %s extracted service None and creator %s", value, value)
    return None, value


def append_creator(creator: Creator):
    """Append a creator to the creators.txt file
    Creators.txt hold all creators used in refresh command"""
    line = f"{creator.service}/{creator.id}"
    lines = load_txt(Config.CREATORS_FILE)

    if line in lines:
        return
    lines.append(line)
    write_txt(Config.CREATORS_FILE, line, mode="a")
