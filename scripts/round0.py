"""
Created on 2026-11-18

@author: wf

Round 0 of the Semantic Long Tail report, see SemanticLongTail #1: generate the
record and the page of each volume of a CEUR-WS www directory into a year tree
by ceursemantify --generate, one call per volume, and log per volume what
happened; standard library only, run with python3 -I; the www directory is
only read

usage: python3 -I round0.py --www <www> --tree <tree> --log <log.jsonl>
       --ceursemantify <path> [--pubyear YYYY ...] [--all] [volumes ...]
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional

# python3 -I does not put the script directory on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ceurpages import write_result  # noqa: E402

PUBDATE_PATTERN = re.compile(r"class\s*=\s*[\"']?CEURPUBDATE[\"']?[^>]*>([^<]*)<", re.I)
YEAR_PATTERN = re.compile(r"\b(19\d\d|20\d\d)\b")
STATE_PATTERN = re.compile(r"<!--\s*CEURSTATE=(\w+)")
VOLUME_DIR_PATTERN = re.compile(r"Vol-(\d+)")
YEAR_DIR_PATTERN = re.compile(r"\d{4}")


def parse_volumes(specs: List[str]) -> List[int]:
    """
    parse volume numbers and ranges such as 1500 or 15-25

    Args:
        specs: the numbers and ranges

    Returns:
        List[int]: the volume numbers
    """
    numbers: List[int] = []
    for spec in specs:
        if "-" in spec:
            first, last = spec.split("-", 1)
            numbers.extend(range(int(first), int(last) + 1))
        else:
            numbers.append(int(spec))
    return numbers


def all_volumes(www: str) -> List[int]:
    """
    get the numbers of all directories Vol-N of the www directory that hold an index.html

    Args:
        www: the directory holding Vol-N/index.html

    Returns:
        List[int]: the volume numbers in order
    """
    numbers = []
    for name in os.listdir(www):
        match = VOLUME_DIR_PATTERN.fullmatch(name)
        if match and os.path.isfile(os.path.join(www, name, "index.html")):
            numbers.append(int(match.group(1)))
    numbers.sort()
    return numbers


def read_page(www: str, number: int) -> Optional[str]:
    """
    read the index.html of the given volume

    Args:
        www: the directory holding Vol-N/index.html
        number: the volume number

    Returns:
        Optional[str]: the html text or None if there is no page
    """
    html = None
    path = os.path.join(www, f"Vol-{number}", "index.html")
    if os.path.isfile(path):
        with open(path, "rb") as html_file:
            html = html_file.read().decode("utf-8", errors="replace")
    return html


def publication_year(html: str) -> Optional[int]:
    """
    get the year of the CEURPUBDATE mark of the page

    Args:
        html: the page

    Returns:
        Optional[int]: the year or None if the page has no such mark with a year
    """
    year = None
    match = PUBDATE_PATTERN.search(html)
    if match:
        year_match = YEAR_PATTERN.search(match.group(1))
        if year_match:
            year = int(year_match.group(1))
    return year


def select_volumes(www: str, specs: List[str], pubyears: List[int], take_all: bool) -> List[int]:
    """
    select the volumes to run on

    Args:
        www: the directory holding Vol-N/index.html
        specs: volume numbers and ranges
        pubyears: publication years whose volumes are taken by their CEURPUBDATE mark
        take_all: take all volumes

    Returns:
        List[int]: the selected volume numbers that have a page, in order
    """
    present = all_volumes(www)
    if take_all:
        selected = set(present)
    else:
        selected = set(parse_volumes(specs)) & set(present)
        if pubyears:
            for number in present:
                html = read_page(www, number)
                if html and publication_year(html) in pubyears:
                    selected.add(number)
    volumes = sorted(selected)
    return volumes


def tool_version(ceursemantify: str) -> str:
    """
    get the version line of ceursemantify

    Args:
        ceursemantify: the path of the command

    Returns:
        str: the version line
    """
    proc = subprocess.run([ceursemantify, "-V"], capture_output=True, text=True)
    version = (proc.stdout + proc.stderr).strip()
    return version


def snapshot_commit(www: str) -> str:
    """
    get the commit of the git repository that holds the www directory

    Args:
        www: the www directory

    Returns:
        str: short hash and commit date
    """
    proc = subprocess.run(
        ["git", "-C", www, "log", "-1", "--format=%h %ad", "--date=iso"],
        capture_output=True,
        text=True,
    )
    commit = proc.stdout.strip()
    return commit


def generated_year(tree: str, number: int) -> Optional[str]:
    """
    find the year directory of the tree into which the page of the volume was generated

    Args:
        tree: the output directory holding the year directories
        number: the volume number

    Returns:
        Optional[str]: the year directory name or None if no page was generated
    """
    year = None
    if os.path.isdir(tree):
        for name in sorted(os.listdir(tree)):
            if YEAR_DIR_PATTERN.fullmatch(name):
                if os.path.isfile(os.path.join(tree, name, f"Vol-{number}", "index.html")):
                    year = name
    return year


def sanitize(text: str, www: str, tree: str, limit: int) -> str:
    """
    replace the local paths in the given tool output and shorten it

    Args:
        text: the tool output
        www: the www directory, written as <www>
        tree: the output directory, written as <tree>
        limit: maximum number of characters kept from the end

    Returns:
        str: the sanitized text
    """
    clean = text.replace(www, "<www>").replace(tree, "<tree>").strip()
    if len(clean) > limit:
        clean = "..." + clean[-limit:]
    return clean


def run_volume(ceursemantify: str, www: str, tree: str, number: int, timeout: int, context: Dict) -> Dict:
    """
    generate one volume into the tree and describe the result

    Args:
        ceursemantify: the path of the command
        www: the directory holding Vol-N/index.html
        tree: the output directory holding the year directories
        number: the volume number
        timeout: seconds before the call is stopped
        context: version and snapshot written into the row

    Returns:
        Dict: the log row of the volume
    """
    html = read_page(www, number) or ""
    state_match = STATE_PATTERN.search(html)
    pub_year = publication_year(html)
    command = [ceursemantify, "--generate", os.path.join(www, f"Vol-{number}"), "-o", tree]
    start = time.monotonic()
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        returncode = proc.returncode
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        returncode = None
        output = f"timeout after {timeout} s"
    seconds = round(time.monotonic() - start, 2)
    tree_year = generated_year(tree, number)
    if returncode != 0:
        status = "failed"
    elif tree_year:
        status = "generated"
    else:
        status = "skipped"
    lines = [line for line in output.splitlines() if line.strip()]
    if tree_year:
        year, year_source = tree_year, "tree"
    elif pub_year:
        year, year_source = str(pub_year), "publication-inferred"
    else:
        year, year_source = None, "none"
    row = {
        "volume": number,
        "status": status,
        "returncode": returncode,
        "message": sanitize(lines[-1] if lines else "", www, tree, 300),
        "output": sanitize(output, www, tree, 4000),
        "seconds": seconds,
        "year": year,
        "year_source": year_source,
        "tree_year": tree_year,
        "pub_year": pub_year,
        "ceurstate": state_match.group(1) if state_match else None,
        "has_orig": os.path.isfile(os.path.join(www, f"Vol-{number}", "index.html.orig")),
        **context,
    }
    return row


def summarize(rows: List[Dict], total_volumes: int, context: Dict) -> Dict:
    """
    count the results per year and status and estimate the run time for all volumes

    Args:
        rows: the log rows
        total_volumes: the number of volumes of the www directory
        context: version and snapshot

    Returns:
        Dict: the summary
    """
    per_year: Dict[str, Dict[str, int]] = {}
    per_status: Dict[str, int] = {}
    for row in rows:
        year = row["year"] or "none"
        counts = per_year.setdefault(year, {"generated": 0, "failed": 0, "skipped": 0})
        counts[row["status"]] += 1
        per_status[row["status"]] = per_status.get(row["status"], 0) + 1
    seconds = sum(row["seconds"] for row in rows)
    mean = seconds / len(rows) if rows else 0.0
    summary = {
        **context,
        "volumes": len(rows),
        "per_status": per_status,
        "per_year": dict(sorted(per_year.items())),
        "year_sources": {
            source: sum(1 for row in rows if row["year_source"] == source)
            for source in ("tree", "publication-inferred", "none")
        },
        "seconds": round(seconds, 1),
        "seconds_per_volume": round(mean, 2),
        "volumes_in_www": total_volumes,
        "estimate_hours_all": round(mean * total_volumes / 3600, 2),
        "failures": [{"volume": row["volume"], "message": row["message"]} for row in rows if row["status"] == "failed"],
        "skips": [{"volume": row["volume"], "message": row["message"]} for row in rows if row["status"] == "skipped"],
    }
    return summary


def main() -> None:
    """
    run ceursemantify --generate on the selected volumes and write the log and the summary
    """
    parser = argparse.ArgumentParser(description="Round 0: generate all volumes into a year tree")
    parser.add_argument("--www", required=True, help="directory holding Vol-N/index.html, only read")
    parser.add_argument("--tree", required=True, help="output directory of the year tree")
    parser.add_argument("--log", required=True, help="per volume log as JSON lines")
    parser.add_argument("--summary", help="summary JSON, default: the log path with .summary.json")
    parser.add_argument("--ceursemantify", required=True, help="path of the ceursemantify command")
    parser.add_argument("--pubyear", type=int, action="append", default=[], help="take the volumes of this year")
    parser.add_argument("--all", action="store_true", help="take all volumes")
    parser.add_argument("--timeout", type=int, default=600, help="seconds per volume")
    parser.add_argument("volumes", nargs="*", help="volume numbers and ranges, e.g. 15-25")
    args = parser.parse_args()
    www = os.path.abspath(args.www)
    tree = os.path.abspath(args.tree)
    os.makedirs(tree, exist_ok=True)
    context = {
        "version": tool_version(args.ceursemantify),
        "snapshot": snapshot_commit(www),
        "run": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    volumes = select_volumes(www, args.volumes, args.pubyear, args.all)
    sys.stderr.write(f"{len(volumes)} volumes, {context}\n")
    rows = []
    with open(args.log, "w", encoding="utf-8") as log_file:
        for index, number in enumerate(volumes, 1):
            row = run_volume(args.ceursemantify, www, tree, number, args.timeout, context)
            rows.append(row)
            log_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            log_file.flush()
            sys.stderr.write(f"{index}/{len(volumes)} Vol-{number} {row['status']} {row['seconds']} s\n")
    summary = summarize(rows, len(all_volumes(www)), context)
    summary_path = args.summary or re.sub(r"\.jsonl$", "", args.log) + ".summary.json"
    write_result(summary, summary_path)


if __name__ == "__main__":
    main()
