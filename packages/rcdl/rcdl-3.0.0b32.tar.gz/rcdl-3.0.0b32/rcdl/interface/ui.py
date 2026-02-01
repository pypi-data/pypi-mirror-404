# interface/ui.py

import logging
import click
from rich.console import Console, Group
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich import box
from rich.live import Live
from rich.text import Text
from rcdl.core.models import Creator, FusedStatus, Status


class NestedProgress:
    def __init__(self, console: Console):
        self.console = console
        self.global_progress: Progress | None = None
        self.current_progress: Progress | None = None
        self.live: Live | None = None

        self.total_task: int | None = None
        self.current_task: int | None = None
        self.status_text = Text("", style="cyan")
        self.current_label = ""

    def start(
        self, *, total: int, total_label: str = "Total", current_label: str = "Current"
    ):
        # Global progress (elapsed only)
        self.global_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )

        # Current task progress (ETA included)
        self.current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )

        self.current_label = current_label
        group = Group(self.global_progress, self.current_progress, self.status_text)
        self.live = Live(group, console=self.console)
        self.live.__enter__()

        self.total_task = self.global_progress.add_task(total_label, total=total)
        self.current_task = self.current_progress.add_task(
            current_label, total=1, visible=False
        )

    # total task helpers
    def advance_total(self, step: int = 1):
        if self.global_progress and self.total_task is not None:
            self.global_progress.advance(self.total_task, step)  # type: ignore

    def reset_current(self):
        if not self.current_progress or self.current_task is None:
            return

        self.current_progress.remove_task(self.current_task)  # type: ignore

        self.current_task = self.current_progress.add_task(
            self.current_label,
            total=1,
            visible=False,
        )

    def start_current(self, description: str, total: int | None = None):
        if not self.current_progress or self.current_task is None:
            return

        self.reset_current()

        self.current_progress.update(
            self.current_task,  # type: ignore
            description=description,
            total=total or 1,
            completed=0,
            visible=True,
        )

    def advance_current(self, step: int | float = 1):
        if self.current_progress and self.current_task is not None:
            self.current_progress.advance(self.current_task, step)  # type: ignore

    def finish_current(self):
        if self.current_progress and self.current_task is not None:
            self.current_progress.update(self.current_task, visible=False)  # type: ignore

    # Status line
    def set_status(self, cyan: str, green: str = ""):
        self.status_text.plain = ""
        self.status_text.append(cyan, style="cyan")
        if green:
            self.status_text.append(green, style="green")

    # Close
    def close(self):
        if self.live:
            self.live.__exit__(None, None, None)
            self.live = None


class UI:
    console = Console()
    logger = logging.getLogger()

    _video_progress_text: Text | None = None
    _concat_progress_text: Text | None = None
    _live: Live | None = None
    _generic_text: Text | None = None

    @staticmethod
    def _log_to_file(log_level, msg: str):
        log_level(msg)

    @classmethod
    def success(cls, msg: str):
        """Print success msg"""
        cls.console.print(f"[green]{msg}[/]")

    @classmethod
    def info(cls, msg: str):
        """Print & log info msg"""
        cls.console.print(msg)
        cls._log_to_file(cls.logger.info, msg)

    @classmethod
    def debug(cls, msg: str):
        """Log debug msg"""
        # cls.console.print(f"[dim]{msg}[/]")
        cls._log_to_file(cls.logger.debug, msg)

    @classmethod
    def warning(cls, msg: str):
        """Print & log warning msg"""
        cls.console.print(f"[yellow]{msg}[/]")
        cls._log_to_file(cls.logger.debug, msg)

    @classmethod
    def error(cls, msg: str):
        """Print & log error msg"""
        cls.console.print(f"[red]{msg}[/]")
        cls._log_to_file(cls.logger.debug, msg)

    @classmethod
    def table_creators(cls, creators: list[Creator]):
        """Print to cli a table with all creators in creators.txt. Format is Creator ID | Service"""
        table = Table(title="Creators", box=box.MINIMAL, show_lines=True)
        table.add_column("Creators ID")
        table.add_column("Service")
        for creator in creators:
            table.add_row(creator.id, creator.service)
        cls.console.print(table)

    @classmethod
    def progress_posts_fetcher(cls, max_pages: int):
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=cls.console,
            transient=False,  # remove progress bar after finish
        )
        return progress


def print_db_info(info: dict):
    click.echo("--- TABLES ---")
    click.echo("Posts:")
    click.echo(f"\t{info['posts']} total")
    click.echo("FusedMedias:")
    for status in FusedStatus:
        click.echo(f"\t{info['fuses'][status]} {status}")
    click.echo("Medias:")
    for status in Status:
        click.echo(f"\t{info['medias'][status]} {status}")
