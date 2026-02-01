# interface/cli.py

"""Hold all cli commands"""

import logging
import subprocess
import sys
import inspect

import click

from rcdl.core import downloader as dl
from rcdl.interface.ui import UI, print_db_info
from rcdl.core.fuse import fuse_medias
from rcdl.core.opti import optimize
from rcdl.core.config import Config
from rcdl.core.parser import (
    get_creators,
    get_creator_from_line,
    parse_creator_input,
    append_creator,
)
from rcdl.core.db import DB
from rcdl.utils import clean_all

from rcdl import __version__


@click.command(help="Refresh video to be downloaded")
@click.option(
    "--max-fail-count",
    type=int,
    help="Set maximum number of failed attempts. Take precedence over config.toml",
)
def refresh(max_fail_count: int | None):
    """Refresh database with creators videos

    - get all creators from creators.txt
    - for each creators find all videos and put them in the database
    No download is done in this command
    """

    UI.info("Welcome to RCDL refresh")
    dl.refresh_creators_videos()

    with DB() as db:
        info = db.get_nb_per_status()
    print_db_info(info)


@click.command(help="Download all videos from all creator")
@click.option(
    "--max-fail-count",
    type=int,
    help="Set maximum number of failed attempts. Take precedence over config.toml",
)
def dlsf(max_fail_count: int | None):
    """Download video based on DB information

    - read databse
    - for each video NOT_DOWNLOADED or FAILED & fail_count < settings, dl video
    """
    UI.info("Welcome to RCDL dlsf")
    dl.download_videos_to_be_dl(max_fail_count)


@click.command("fuse", help="Fuse part video into one")
def fuse():
    """Fuse videos"""
    UI.info("Fuse/Concat video together")
    fuse_medias()


@click.command(help="Optimized video size")
def opti():
    """Optimized video size"""
    UI.info("Optimized video")
    optimize()


@click.command(help="Clean patial download file, cache, etc...")
@click.option("--all", is_flag=True, help="Act as if al lthe flags are true")
@click.option(
    "--partial", is_flag=True, help="Remove partial file from download (.aria2, .part)"
)
@click.option(
    "--cache", is_flag=True, help="remove cache from yt-dlp and kill aria2 process"
)
@click.option(
    "--medias-deleted",
    is_flag=True,
    help="Remove media marked for deletion (TO_BE_DELETED status)",
)
def clean(all: bool, partial: bool, cache: bool, medias_deleted: bool):
    """Remove partial download, clear subprocesses cache"""
    clean_all(all, partial, cache, medias_deleted)


@click.command(help="Discover videos/creators with tags")
@click.option("--tag", required=True, type=str, help="Tag to search for")
@click.option(
    "--max-page", default=10, type=int, help="Maximum number of pages to fetch"
)
def discover(tag, max_page):
    """Discover new creators/videos
    currently WIP. Do not use in prod"""
    msg = f"[cdl] discover with tag={tag} max_page={max_page}"
    click.echo(msg)
    logging.info(msg)
    UI.info("WIP - UNIMPLEMENTED")


@click.command("add", help="Add a creator")
@click.argument("creator_input")
def add_creator(creator_input):
    """Add a creator (URL or str) to creators.txt"""
    service, creator_id = parse_creator_input(creator_input)
    line = f"{service}/{creator_id}"
    creator = get_creator_from_line(line)
    if creator is not None:
        append_creator(creator)
        UI.info(f"Added {line} to creators.txt")
    else:
        UI.warning("Could not extract creator from input. Please check input is valid")


@click.command("remove", help="Remove a creator")
@click.option("--db", is_flag=True)
@click.argument("creator_input")
def remove_creator(db, creator_input):
    """Remove a creator (excat line) from creators.txt"""
    _service, creator_id = parse_creator_input(str(creator_input))

    creators = get_creators()
    all_creators = []
    matched_creator = None
    for creator in creators:
        if creator.id == creator_id:
            matched_creator = creator
            continue
        all_creators.append(creator)

    if matched_creator is None:
        UI.error(f"Could not find creator from {creator_input}")
        return

    try:
        with open(Config.CREATORS_FILE, "w", encoding="utf-8"):
            pass
    except OSError as e:
        UI.error(
            f"Failed to create creators file at {Config.CREATORS_FILE} due to: {e}"
        )
        return
    for c in all_creators:
        append_creator(c)
    UI.info(f"Removed creator {matched_creator.id}@({matched_creator.service})")
    if db:
        UI.info("Not yet implemented")


@click.command("list", help="List all creators")
def list_creators():
    """List all creators in creators.txt"""
    creators = get_creators()
    UI.table_creators(creators)


@click.command("status", help="Print db info")
def db_status():
    """Print number of entry per status per tables in the database"""
    with DB() as db:
        info = db.get_nb_per_status()
    print_db_info(info)


@click.command("gui", help="Launch GUI")
def launch_gui():
    UI.info("Launching GUI...")
    Config.set_host()

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "rcdl.gui.video_server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8123",
            "--log-level",
            "warning",
        ]
    )

    import importlib.resources as resources

    gui_path = resources.files("rcdl.gui").joinpath("gui.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(gui_path)])


@click.command("show-config")
def show_config():
    """Show all value in Config"""
    for name, value in vars(Config).items():
        if not name.startswith("__") and not inspect.isroutine(value):
            UI.success(f"{name}: {value}")


# --- CLI GROUP ---
@click.group()
@click.option("--debug", is_flag=True)
@click.option("--dry-run", is_flag=True)
@click.version_option(version=__version__, prog_name=Config.APP_NAME)
def cli(debug, dry_run):
    """Init cli app. Assign Config var depending on flag used when calling prgm"""
    Config.set_debug(debug)
    Config.set_dry_run(dry_run)


# main commands
cli.add_command(dlsf)
cli.add_command(discover)
cli.add_command(refresh)
cli.add_command(fuse)
cli.add_command(opti)
cli.add_command(launch_gui)

# creators command
cli.add_command(add_creator)
cli.add_command(remove_creator)
cli.add_command(list_creators)

# helper command
cli.add_command(clean)
cli.add_command(db_status)
cli.add_command(show_config)
