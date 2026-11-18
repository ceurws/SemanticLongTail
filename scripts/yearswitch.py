"""
Created on 2026-11-18

@author: wf

Year switch table of the CEUR-WS volumes, see SemanticLongTail #1 and
ceurws/semantify #78: volume numbers are given in the order of publication, so
the first volume number of each publication year gives the publication year of
every volume by lookup; the volumes that the lookup puts into another year than
their reference year are listed as exceptions

Method:
- reference year of a volume: the year of its CEURPUBDATE mark (pub_year of the
  round 0 log); a volume without it takes the year of the fallback source
- fallback sources, both read from the file modification times of the volume
  directory in the www copy, which the mirror rsync -avz keeps:
  orig: modification time of Vol-N/index.html.orig
  oldest: oldest modification time of all regular files below Vol-N
- the switch of a year is the volume number with the fewest differences to the
  reference years of that year and the year before
- check: each source is compared with the CEURPUBDATE year where both exist and
  with the publication year ranges of the volume browser for 1995 to 2009
  given in ceurws/semantify #26

Standard library only, run with python3 -I; the www directory is only read.

usage: python3 -I yearswitch.py --www <www> --log <round0.jsonl> --out <yearswitch.json>
"""

import argparse
import bisect
import datetime
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

VOLUME_DIR_PATTERN = re.compile(r"Vol-(\d+)")

# publication year ranges of the volume browser, table of 2026-10-02 in
# ceurws/semantify #26; 2007 and 2008 overlap there
VOLUME_BROWSER_RANGES: List[Tuple[int, int, int]] = [
    (1995, 1, 1),
    (1996, 2, 7),
    (1997, 8, 8),
    (1998, 9, 14),
    (1999, 15, 25),
    (2000, 26, 35),
    (2001, 36, 52),
    (2002, 53, 65),
    (2003, 66, 90),
    (2004, 91, 124),
    (2005, 125, 168),
    (2006, 169, 225),
    (2007, 226, 378),
    (2008, 304, 431),
    (2009, 432, 689),
]

FALLBACKS = ["orig", "oldest"]


def mtime_year(path: str) -> Optional[int]:
    """
    year of the modification time of a file

    Args:
        path: the file

    Returns:
        the year or None if the file does not exist
    """
    year = None
    if os.path.isfile(path):
        year = datetime.datetime.fromtimestamp(os.path.getmtime(path)).year
    return year


def oldest_year(volume_dir: str) -> Optional[int]:
    """
    year of the oldest modification time of all regular files below a directory

    Args:
        volume_dir: the volume directory

    Returns:
        the year or None if there is no file
    """
    oldest = None
    for root, _dirs, files in os.walk(volume_dir):
        for name in files:
            path = os.path.join(root, name)
            if os.path.isfile(path) and not os.path.islink(path):
                mtime = os.path.getmtime(path)
                if oldest is None or mtime < oldest:
                    oldest = mtime
    year = None
    if oldest is not None:
        year = datetime.datetime.fromtimestamp(oldest).year
    return year


def read_volumes(www: str, log: str) -> Dict[int, Dict[str, Optional[int]]]:
    """
    read the years of every volume directory Vol-N with index.html

    Args:
        www: the www directory of the copy
        log: the round 0 log with pub_year per volume

    Returns:
        volume number to its years pubdate, orig and oldest
    """
    pub_years = {}
    with open(log, encoding="utf-8") as log_file:
        for line in log_file:
            row = json.loads(line)
            pub_years[row["volume"]] = row.get("pub_year")
    volumes = {}
    for name in os.listdir(www):
        match = VOLUME_DIR_PATTERN.fullmatch(name)
        volume_dir = os.path.join(www, name)
        if match and os.path.isfile(os.path.join(volume_dir, "index.html")):
            number = int(match.group(1))
            volumes[number] = {
                "pubdate": pub_years.get(number),
                "orig": mtime_year(os.path.join(volume_dir, "index.html.orig")),
                "oldest": oldest_year(volume_dir),
            }
    return volumes


def switch_table(years: List[Tuple[int, int]]) -> Dict[int, int]:
    """
    first volume number of each year with the fewest differences to the
    reference years of that year and the year before

    Args:
        years: sorted pairs of volume number and reference year

    Returns:
        year to its first volume number
    """
    year_list = sorted(set(year for _volume, year in years))
    table = {year_list[0]: min(volume for volume, year in years if year == year_list[0])}
    for before, year in zip(year_list, year_list[1:]):
        pair = [(volume, y) for volume, y in years if y in (before, year)]
        candidates = sorted(set(volume for volume, y in pair if y == year))
        best = None
        for start in candidates:
            differences = sum(1 for v, y in pair if (y == before and v >= start) or (y == year and v < start))
            if best is None or differences < best[0]:
                best = (differences, start)
        table[year] = best[1]
    return table


def lookup(table: Dict[int, int], volume: int) -> int:
    """
    publication year of a volume by the switch table

    Args:
        table: year to its first volume number
        volume: the volume number

    Returns:
        the year
    """
    year_list = sorted(table)
    starts = [table[year] for year in year_list]
    index = max(bisect.bisect_right(starts, volume) - 1, 0)
    year = year_list[index]
    return year


def browser_years(volume: int) -> List[int]:
    """
    publication years of a volume by the volume browser ranges of semantify #26

    Args:
        volume: the volume number

    Returns:
        the years whose range holds the volume, empty beyond Vol-689
    """
    years = [year for year, first, last in VOLUME_BROWSER_RANGES if first <= volume <= last]
    return years


def evaluate(volumes: Dict[int, Dict[str, Optional[int]]], fallback: str) -> Dict:
    """
    switch table, exceptions and checks for one fallback source

    Args:
        volumes: volume number to its years
        fallback: the source for volumes without CEURPUBDATE

    Returns:
        the result for this fallback
    """
    reference = []
    source_count = {"pubdate": 0, fallback: 0, "none": 0}
    for number in sorted(volumes):
        years = volumes[number]
        year = years["pubdate"]
        source = "pubdate"
        if year is None:
            year = years[fallback]
            source = fallback
        if year is None:
            source = "none"
        source_count[source] += 1
        if year is not None:
            reference.append((number, year))
    table = switch_table(reference)
    exceptions = [
        {"volume": number, "reference": year, "lookup": lookup(table, number)}
        for number, year in reference
        if lookup(table, number) != year
    ]
    in_browser = [number for number, _year in reference if browser_years(number)]
    browser_differences = [
        {"volume": number, "lookup": lookup(table, number), "browser": browser_years(number)}
        for number in in_browser
        if lookup(table, number) not in browser_years(number)
    ]
    result = {
        "fallback": fallback,
        "sources": source_count,
        "table": {str(year): table[year] for year in sorted(table)},
        "exceptions": exceptions,
        "browser_compared": len(in_browser),
        "browser_differences": browser_differences,
    }
    return result


def source_agreement(volumes: Dict[int, Dict[str, Optional[int]]]) -> Dict:
    """
    agreement of each fallback source with CEURPUBDATE and with the volume
    browser ranges

    Args:
        volumes: volume number to its years

    Returns:
        per source the counts compared and same year
    """
    agreement = {}
    for source in FALLBACKS:
        pub_pairs = [(y["pubdate"], y[source]) for y in volumes.values() if y["pubdate"] and y[source]]
        browser_pairs = [(browser_years(n), y[source]) for n, y in volumes.items() if browser_years(n) and y[source]]
        agreement[source] = {
            "pubdate_compared": len(pub_pairs),
            "pubdate_same_year": sum(1 for a, b in pub_pairs if a == b),
            "browser_compared": len(browser_pairs),
            "browser_same_year": sum(1 for a, b in browser_pairs if b in a),
        }
    return agreement


def main() -> None:
    """
    command line entry
    """
    parser = argparse.ArgumentParser(description="year switch table of the CEUR-WS volumes")
    parser.add_argument("--www", required=True, help="www directory of the copy, only read")
    parser.add_argument("--log", required=True, help="round 0 log with pub_year per volume")
    parser.add_argument("--out", required=True, help="result json")
    parser.add_argument("--snapshot", default="", help="commit of the copy the www directory is at")
    args = parser.parse_args()
    volumes = read_volumes(args.www, args.log)
    result = {
        "run": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "snapshot": args.snapshot,
        "volumes": len(volumes),
        "agreement": source_agreement(volumes),
        "results": [evaluate(volumes, fallback) for fallback in FALLBACKS],
    }
    with open(args.out, "w", encoding="utf-8") as out_file:
        json.dump(result, out_file, indent=1)
    for item in result["results"]:
        print(
            f"{item['fallback']}: sources {item['sources']}, {len(item['table'])} years, "
            f"{len(item['exceptions'])} exceptions, browser differences "
            f"{len(item['browser_differences'])} of {item['browser_compared']}"
        )
    print(f"agreement {result['agreement']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
