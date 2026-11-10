"""
Created on 2026-11-10

@author: wf

shared access to the volume pages of a CEUR-WS www directory for the
measurement scripts of the Semantic Long Tail report; standard library only,
so that it runs with python3 -I on a host without packages
"""

import datetime
import json
import os
import re
import sys
from typing import Dict, Iterator, List, Optional, Tuple

TAG_PATTERN = re.compile(r"<[^>]+>")
SPACE_PATTERN = re.compile(r"\s+")


def volume_number(volume_dir: str) -> int:
    """
    get the number of the volume directory

    Args:
        volume_dir: a path ending in Vol-N

    Returns:
        int: N
    """
    number = int(os.path.basename(volume_dir).split("-", 1)[1])
    return number


def volume_pages(www: str) -> Iterator[Tuple[int, str]]:
    """
    iterate over the volume pages of the given www directory in volume order

    Args:
        www: the directory holding Vol-N/index.html

    Yields:
        the volume number and the html text of its index.html
    """
    names = [name for name in os.listdir(www) if re.fullmatch(r"Vol-\d+", name)]
    for name in sorted(names, key=lambda name: int(name.split("-", 1)[1])):
        path = os.path.join(www, name, "index.html")
        if os.path.isfile(path):
            with open(path, "rb") as html_file:
                html = html_file.read().decode("utf-8", errors="replace")
            yield volume_number(path.rsplit("/", 1)[0]), html


def text_of(html: str) -> str:
    """
    get the text of the given html fragment with whitespace collapsed

    Args:
        html: the fragment

    Returns:
        str: the text
    """
    text = SPACE_PATTERN.sub(" ", TAG_PATTERN.sub(" ", html)).strip()
    return text


def snapshot(www: str) -> Dict[str, str]:
    """
    describe the snapshot the measurement runs on

    Args:
        www: the directory holding the volumes

    Returns:
        Dict[str, str]: the run date and the newest index.html modification time
    """
    newest = 0.0
    for name in os.listdir(www):
        path = os.path.join(www, name, "index.html")
        if os.path.isfile(path):
            newest = max(newest, os.path.getmtime(path))
    description = {
        "run": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "newest_page": datetime.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M"),
        "host_script_version": "2026-11-10",
    }
    return description


def histogram(values: List, key=None) -> Dict[str, int]:
    """
    count the given values

    Args:
        values: the values
        key: optional function mapping a value to its bin

    Returns:
        Dict[str, int]: bin to count, sorted by count descending
    """
    counts: Dict[str, int] = {}
    for value in values:
        bin_value = str(key(value) if key else value)
        counts[bin_value] = counts.get(bin_value, 0) + 1
    sorted_counts = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return sorted_counts


def write_result(result: Dict, path: Optional[str]) -> None:
    """
    write the result as JSON to the given path or to stdout

    Args:
        result: the result
        path: the file path or None
    """
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if path:
        with open(path, "w", encoding="utf-8") as out_file:
            out_file.write(text)
    else:
        sys.stdout.write(text + "\n")
