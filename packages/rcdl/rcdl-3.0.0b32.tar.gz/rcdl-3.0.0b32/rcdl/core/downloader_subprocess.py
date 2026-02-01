# core/downloader_subprocess.py

"""
Handle all subprocess call to external tool (yt-dlp, ffmpeg, ...)
"""

import subprocess
import logging
from pathlib import Path
import os


from rcdl.interface.ui import UI, NestedProgress
from rcdl.core import parser
from rcdl.core.models import Media, Post
from rcdl.core.config import Config
from rcdl.utils import bytes_to_str


def ytdlp_clear_cache():
    """Clear yt-dlp cache"""
    cmd = ["yt-dlp", "--rm-cache-dir"]
    subprocess.run(cmd, check=False)


def kill_aria2c():
    """Kill all aria2c process"""
    cmd = ["pkill", "-f", "aria2c"]
    subprocess.run(cmd, check=False)


def ytdlp_subprocess(
    url: str,
    filepath: Path | str,
):
    """Call yt-dlp in a subprocess to download a video"""

    cmd = [
        "yt-dlp",
        "-q",
        "--progress",
        url,
        "-o",
        filepath,
        "--external-downloader",
        "aria2c",
    ]

    logging.info("CMD: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logging.error("yt-dlp failed to dl vid: %s", result.stderr)

    return result.returncode


def ffprobe_get_duration(path: Path) -> int | None:
    """Get duration of a video in seconds with ffprobe
    Return an int or None if command failed"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        return int(float(result.stdout.strip()))
    except subprocess.CalledProcessError as e:
        UI.error(f"Failed to use ffprobe on {path} due to {e}")
        return None
    except (AttributeError, ValueError, OverflowError) as e:
        UI.error(f"Failed to parse duration result of {path} due to {e}")
        return None


def get_max_width_height(medias: list[Media], post: Post) -> tuple[int, int]:
    """Get width and height of all media in list. Return max within video found and config"""

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0",
    ]
    width = 0
    height = 0
    max_width = 1920
    max_height = 1080
    for m in medias:
        path = os.path.join(Config.creator_folder(post.user), m.file_path)
        full_cmd = cmd + [path]

        try:
            result = subprocess.run(
                full_cmd, capture_output=True, text=True, check=True
            )
            w_str, h_str = result.stdout.strip().split(",")

            width = min(int(w_str), max_width)
            height = min(int(h_str), max_height)
        except subprocess.CalledProcessError as e:
            UI.error(f"Fail to use ffprobe to get width, height on {path} due to {e}")
        except (AttributeError, ValueError, OverflowError) as e:
            UI.error(f"Failed to parse duration for {path} due to {e}")
    return (width, height)


def get_total_duration(medias: list[Media], post: Post) -> int:
    """Get total duration in ms of all medias in list"""

    def _get_duration(path: str) -> int:
        """Get video duration in ms"""

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(float(result.stdout.strip()) * 1000)

    duration = 0
    for m in medias:
        path = os.path.join(Config.creator_folder(post.user), m.file_path)
        duration += _get_duration(path)
    return duration


def ffmpeg_concat_build_command(medias: list[Media], post: Post) -> dict:
    """Build the ffmpeg concat command"""

    width, height = get_max_width_height(medias, post)
    logging.info("Found (%s, %s) (width, height) for this group.", width, height)
    if width == 0:
        width = Config.MAX_WIDTH
    if height == 0:
        height = Config.MAX_HEIGHT

    # output path
    output_filename = parser.get_filename_fuse(post)
    output_path = os.path.join(Config.creator_folder(post.user), output_filename)

    # build cmd
    cmd = ["ffmpeg", "-y", "-progress", "pipe:2", "-nostats"]

    # inputs
    for media in medias:
        input_path = os.path.join(Config.creator_folder(post.user), media.file_path)
        cmd.extend(["-i", input_path])

    # filter complex
    filter_lines = []
    for idx in range(len(medias)):
        filter_lines.append(
            f"[{idx}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={Config.FPS},setsar=1"
            f"[v{idx}]"
        )

    # concat inputs
    concat = []
    for idx in range(len(medias)):
        concat.append(f"[v{idx}][{idx}:a]")

    filter_lines.append(f"{''.join(concat)}concat=n={len(medias)}:v=1:a=1[outv][outa]")
    filter_complex = ";".join(filter_lines)

    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            Config.PRESET,
            "-threads",
            str(Config.THREADS),
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            output_path,
        ]
    )

    return {"cmd": cmd, "output_path": output_path}


def parse_line_ffmpeg_concat_into_advance(line: str) -> int | None:
    line = line.strip()
    if not line:
        return None

    progres_key = "out_time_ms"
    if line.startswith(progres_key):
        current_progress_str = line.replace(f"{progres_key}=", "").strip()
        try:
            current_progress_us = int(current_progress_str)
            current_progress_ms = current_progress_us // 1000
            return current_progress_ms
        except ValueError as e:
            logging.warning(
                "Skipping invalid progress line: %r (%s)",
                current_progress_str,
                e,
            )
            return None
        except Exception as e:
            UI.error(f"Unexpected error while updating progress: {e}")
            return None
    return None


def ffmpeg_concat(medias: list[Media], post: Post, progress: NestedProgress):
    """Run ffmpeg concat command to merge video together"""

    command_builder = ffmpeg_concat_build_command(medias, post)
    cmd = command_builder["cmd"]

    logging.info("CMD: %s", " ".join(cmd))

    ffmpeg_log = Config.CACHE_DIR / "ffmpeg.log"
    with open(ffmpeg_log, "w", encoding="utf-8") as log_file:
        print(cmd, file=log_file)
        # run cmd
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        assert process.stderr is not None
        total_duration = get_total_duration(medias, post)
        progress.start_current(
            description=f"{post.user}->{medias[0].file_path}", total=total_duration
        )

        last_progress = 0

        for line in process.stderr:
            line = line.strip()
            print(line, file=log_file)
            current_progress_ms = parse_line_ffmpeg_concat_into_advance(line)
            if current_progress_ms is None:
                continue
            delta = current_progress_ms - last_progress
            progress.advance_current(step=delta)
            last_progress = current_progress_ms

        process.wait()
        progress.finish_current()

    UI.debug(f"Result: {process.returncode}")
    if process.returncode != 0:
        UI.error(f"Failed to concat videos. See ffmpeg log file {ffmpeg_log}")
        with open(ffmpeg_log, "r", encoding="utf-8") as f:
            lines = f.read()
        logging.warning("---FFMPEG LOG---")
        logging.warning(lines)
        logging.warning("---END FFMPEG LOG---")
        return process.returncode

    return 0


def parse_line_into_pourcent(line: str) -> float | None:
    line = line.strip()
    if not line:
        return None

    if "%" in line:
        try:
            parts = line.split("%")
            parts = parts[0].strip().split(" ")
            pourcent = parts[-1]
            flt_prcnt = float(pourcent)
            return flt_prcnt
        except Exception as e:
            UI.error(f"Error parsing line {line}: {e}")
            return None
    return None


def handbrake_optimized(media: Media, user: str, progress: NestedProgress):
    """Optimize video size with handbrake software"""

    handbrake_process = Config.HANDBRAKE_RUN_CMD.split(" ")

    folder_path = Config.creator_folder(user)
    video_path = os.path.join(folder_path, media.file_path)

    output_path = video_path + ".opti.mp4"

    cmd = ["-i", video_path, "-o", output_path, "--preset", "HQ 1080p30 Surround"]

    full_cmd = handbrake_process + cmd
    UI.debug(f"Running cmd '{full_cmd}'")

    # -- process
    process = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    assert process.stdout is not None
    progress.start_current(description="Optimizing", total=100)
    progress.set_status(
        f"{user}@({media.service}) -> ",
        f"{media.file_path} ({bytes_to_str(media.file_size)})",
    )

    current_progress = 0.0

    for line in process.stdout:
        float_pourcent = parse_line_into_pourcent(line)
        if float_pourcent is None:
            continue
        delta = float_pourcent - current_progress
        current_progress = float_pourcent
        progress.advance_current(step=delta)

    process.wait()
    progress.finish_current()
    # -- end process

    if process.returncode == 0:
        UI.debug("Return code: 0")
    else:
        UI.error(f"Return code: {process.returncode}")

    return process.returncode
