# core/file_io.py

"""All write/read to file function (excluding sqlite database)"""

import json


def write_json(path, data, mode="w"):
    """Write dict data to json"""
    with open(path, mode, encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_json(path) -> dict:
    """Load data from json"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_txt(path) -> list[str]:
    """Read text from a .txt file.
    Return list of stripped lines"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        lines[i] = line.strip()
    return lines


def write_txt(path, lines: list[str] | str, mode: str = "a"):
    """Write txt to .txt file"""
    if isinstance(lines, str):
        lines = [lines]

    with open(path, mode, encoding="utf-8") as f:
        for line in lines:
            if not line.endswith("\n"):
                f.write(line + "\n")
            else:
                f.write(line)
