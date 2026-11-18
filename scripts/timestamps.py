"""
Created on 2026-11-18

@author: wf

measure whether the modification times of the files of a volume directory
date the volume: the year of the modification time of index.html, of
index.html.orig and of the oldest file of the directory against the year of
the CEURPUBDATE mark, and the years these files give for the volumes that
Round 0 skipped for want of an event start date, see SemanticLongTail #1 and
semantify #78; standard library only, run with python3 -I on a copy that keeps
the modification times of ceur-ws.org

usage: python3 -I timestamps.py <www> <round0.jsonl> [result.json]
"""

import datetime
import json
import os
import sys
from typing import Dict, List, Optional

# python3 -I does not put the script directory on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ceurpages import histogram, snapshot, write_result  # noqa: E402

KINDS = ["index", "orig", "oldest"]
NO_YEAR = "no event start date"


def mtime_year(path: str) -> Optional[int]:
    """
    get the year of the modification time of the given file

    Args:
        path: the file path

    Returns:
        Optional[int]: the year or None if there is no such file
    """
    year = None
    if os.path.isfile(path):
        year = datetime.datetime.fromtimestamp(os.path.getmtime(path)).year
    return year


def oldest_year(volume_dir: str) -> Optional[int]:
    """
    get the year of the oldest modification time of the files directly in the volume directory

    Args:
        volume_dir: the directory Vol-N

    Returns:
        Optional[int]: the year or None if the directory holds no file
    """
    years = [mtime_year(os.path.join(volume_dir, name)) for name in os.listdir(volume_dir)]
    known = [year for year in years if year is not None]
    year = min(known) if known else None
    return year


def file_years(www: str, number: int) -> Dict[str, Optional[int]]:
    """
    get the years of index.html, index.html.orig and the oldest file of a volume

    Args:
        www: the directory holding Vol-N
        number: the volume number

    Returns:
        Dict[str, Optional[int]]: year per kind
    """
    volume_dir = os.path.join(www, f"Vol-{number}")
    years = {
        "index": mtime_year(os.path.join(volume_dir, "index.html")),
        "orig": mtime_year(os.path.join(volume_dir, "index.html.orig")),
        "oldest": oldest_year(volume_dir),
    }
    return years


def agreement(rows: List[Dict], years_of: Dict[int, Dict[str, Optional[int]]]) -> Dict[str, Dict[str, int]]:
    """
    compare the file years with the CEURPUBDATE year for the volumes that have both

    Args:
        rows: the Round 0 log rows
        years_of: file years per volume

    Returns:
        Dict[str, Dict[str, int]]: per kind the number of volumes compared, with the same year, within one year
    """
    result = {kind: {"compared": 0, "same_year": 0, "within_one_year": 0} for kind in KINDS}
    for row in rows:
        pub_year = row["pub_year"]
        if pub_year:
            for kind in KINDS:
                year = years_of[row["volume"]][kind]
                if year is not None:
                    counts = result[kind]
                    counts["compared"] += 1
                    counts["same_year"] += year == pub_year
                    counts["within_one_year"] += abs(year - pub_year) <= 1
    return result


def main() -> None:
    """
    measure the file years and write the result
    """
    www = sys.argv[1]
    rows = [json.loads(line) for line in open(sys.argv[2], encoding="utf-8")]
    years_of = {row["volume"]: file_years(www, row["volume"]) for row in rows}
    skipped = [row for row in rows if row["status"] == "skipped" and NO_YEAR in row["message"]]
    without_date = [row for row in skipped if not row["pub_year"]]
    result = {
        "snapshot": {**snapshot(www), "round0": rows[0]["snapshot"] if rows else None},
        "volumes": len(rows),
        "agreement_with_pubdate": agreement(rows, years_of),
        "skipped_without_event_date": len(skipped),
        "of_these_without_pubdate": len(without_date),
        "years_of_volumes_without_any_date": {
            kind: histogram([years_of[row["volume"]][kind] for row in without_date]) for kind in KINDS
        },
        "volumes_without_any_date": [{"volume": row["volume"], **years_of[row["volume"]]} for row in without_date],
    }
    write_result(result, sys.argv[3] if len(sys.argv) > 3 else None)


if __name__ == "__main__":
    main()
