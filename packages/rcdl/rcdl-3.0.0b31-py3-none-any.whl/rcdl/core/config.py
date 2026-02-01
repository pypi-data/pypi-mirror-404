# core/config.py

"""
Handle Config init, dependencies check, logging setup,
files and folders structures, config settings parameters init
"""

from pathlib import Path
import logging
import os
import tomllib
import subprocess
import socket

from rcdl.core.file_io import write_txt


class Config:
    """Global app var/parameters"""

    # paths
    APP_NAME = "rcdl"

    BASE_DIR = Path(os.environ.get("RCDL_BASE_DIR", Path.home() / "Videos/rcdl"))

    CACHE_DIR = BASE_DIR / ".cache"
    DB_PATH = CACHE_DIR / "cdl.db"
    LOG_FILE = CACHE_DIR / "cdl.log"
    CREATORS_FILE = CACHE_DIR / "creators.txt"
    DISCOVER_DIR = CACHE_DIR / "discover"
    CONFIG_FILE = CACHE_DIR / "config.toml"

    DEBUG = False
    DRY_RUN = False

    # api settings
    POST_PER_PAGE: int = 50
    DEFAULT_MAX_PAGE: int = 10
    MAX_FAIL_COUNT: int = 7
    TIMEOUT: int = 10

    # fuse settings
    MAX_WIDTH: int = 1920
    MAX_HEIGHT: int = 1080
    FPS: int = 30
    PRESET: str = "veryfast"
    THREADS: int = 0

    HANDBRAKE_RUN_CMD = "HandBrakeCLI"

    CHECKSUM_RETRY = 2

    HOST = "127.0.0.1"

    @classmethod
    def ensure_dirs(cls):
        """Ensure directory exist"""
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.DISCOVER_DIR.mkdir(exist_ok=True)

    @classmethod
    def ensure_files(cls):
        """Ensure file exist, populate default if necessary"""
        files = [cls.DB_PATH, cls.CREATORS_FILE, cls.CONFIG_FILE]
        for file in files:
            if not file.exists():
                file.touch()
                logging.info("Created file %s", file)
                if file == cls.CREATORS_FILE:
                    write_txt(cls.CREATORS_FILE, DEFAULT_CREATORS, mode="w")
                if file == cls.CONFIG_FILE:
                    write_txt(cls.CONFIG_FILE, DEFAULT_CONFIG, mode="w")

    @classmethod
    def creator_folder(cls, creator_id: str) -> Path:
        """Return creator folder path base on user/creator_id"""
        folder = cls.BASE_DIR / creator_id
        folder.mkdir(exist_ok=True)
        return folder

    @classmethod
    def cache_file(cls, filename: str, ext: str = ".json") -> Path:
        """Return filepath of a file in the .cache/ folder"""
        file_name = filename + ext
        file = cls.CACHE_DIR / file_name
        return file

    @classmethod
    def set_debug(cls, debug: bool):
        """Set class variable DEBUG"""
        cls.DEBUG = debug

    @classmethod
    def set_dry_run(cls, dry_run: bool):
        """Set class variable DRY_RUN"""
        cls.DRY_RUN = dry_run

    @classmethod
    def set_host(cls):
        cls.HOST = cls.get_host_ip()

    @staticmethod
    def get_host_ip():
        """
        Returns the LAN IP of the current machine.
        Falls back to 127.0.0.1 if unable to detect.
        """
        try:
            # connect to a dummy address to get the outgoing IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google DNS
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @classmethod
    def load_config(cls):
        """Load config.toml and set class var with value in config.toml"""
        with open(cls.CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        app = data.get("app", {})
        cls.DEFAULT_MAX_PAGE = app.get("default_max_page", cls.DEFAULT_MAX_PAGE)
        cls.MAX_FAIL_COUNT = app.get("max_fail_count", cls.MAX_FAIL_COUNT)
        cls.TIMEOUT = app.get("timeout", cls.TIMEOUT)
        cls.CHECKSUM_RETRY = app.get("checksum_retry", cls.CHECKSUM_RETRY)

        video = data.get("video", {})
        cls.MAX_WIDTH = video.get("max_width", cls.MAX_WIDTH)
        cls.MAX_HEIGHT = video.get("max_height", cls.MAX_HEIGHT)
        cls.FPS = video.get("fps", cls.FPS)
        cls.PRESET = video.get("preset", cls.PRESET)
        cls.THREADS = video.get("threads", cls.THREADS)

        paths = data.get("paths", {})
        if "base_dir" in paths:
            cls.BASE_DIR = Path(
                os.environ.get("RCDL_BASE_DIR", os.path.expanduser(paths["base_dir"]))
            )
            cls.CACHE_DIR = cls.BASE_DIR / ".cache"
        if "handbrake_run_cmd" in paths:
            cls.HANDBRAKE_RUN_CMD = paths.get("handbrake_run_cmd")


def setup_logging(log_file: Path, level: int = 0):
    """Setup logging for rcdl"""
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()  # avoid double handlers if called multiple times

    # loggin format & file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setFormatter(
        logging.Formatter(
            "{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(file_handler)

    # log library warning/errors
    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)  # only show warnings/errors from libraries
    logger.addHandler(stream)


def check_dependencies():
    """Check external program version against last tested working version"""
    for prgrm, info in DEPENDENCIES_TEST_VERSION.items():
        try:
            result = subprocess.run(
                info["cmd"],
                capture_output=True,
                text=True,
                shell=True,
                check=False,
            )
            version = result.stdout.strip()

            if version != info["version"]:
                print(
                    f"Last tested version for {prgrm}:"
                    f" {info['version']} -> yours: {version}"
                )
                if version == "":
                    print(f"{prgrm} is not installed.")
                print(f"Check {prgrm} is installed if your version is empty.")
        except (OSError, subprocess.SubprocessError) as e:
            print(
                f"Failed to check {prgrm} version due to: {e}\nCheck {prgrm} is installed."
            )


DEPENDENCIES_TEST_VERSION = {
    "yt-dlp": {"cmd": "yt-dlp --version", "version": "2025.12.08"},
    "aria2c": {
        "cmd": "aria2c -v | head -n 1",
        "version": "aria2 version 1.37.0",
    },
    "ffmpeg": {
        "cmd": 'ffmpeg -version | sed -n "s/ffmpeg version \\([-0-9.]*\\).*/\\1/p;"',
        "version": "7.1.1-1",
    },
    "handbrake": {
        "cmd": Config.HANDBRAKE_RUN_CMD
        + ' --version 2>&1 | sed -n "s/HandBrake \\([0-9.]*\\).*/\\1/p"',
        "version": "1.9.2",
    },
}


# default creators
DEFAULT_CREATORS = ["boixd/onlyfans"]

# default config params
DEFAULT_CONFIG: str = """\
[app]
default_max_page = 10
max_fail_count = 7
timeout = 10
checksum_retry = 2

[fuse]
max_width = 1920
max_height = 1080
fps = 30
preset = "veryfast"
threads = 0

[paths]
base_dir = "~/Videos/rcdl"
handbrake_run_cmd = "HandBrakeCLI"
"""
