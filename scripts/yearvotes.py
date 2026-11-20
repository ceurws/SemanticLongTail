"""
Created on 2026-11-20

@author: wf

votes of ten sources on the year of each volume, the requirement being the
publication year on CEUR-WS, and the histograms of their agreement, see
SemanticLongTail #1; standard library only, run with python3 -I on a copy that
keeps the modification times of ceur-ws.org

sources:
    pubdate    year of the CEURPUBDATE mark
    submitted  year of the date of the submitted by line
    browser    year of the publication date of the volume browser data
    orig       year of the modification time of index.html.orig
    oldest     year of the modification time of the oldest file of the volume
    index      year of the modification time of index.html
    pubyear    the CEURPUBYEAR mark
    event      year of the event start date, the tree year of the Round 0 log
               where the log does not say the year was inferred
    title      year in the acronym, else in the title, four digits or 'NN
    neighbours median of the pubdate years of the 25 volumes on each side
"""

import argparse
import json
import os
import re
import statistics
import sys
from typing import Dict, List, Optional

# python3 -I does not put the script directory on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ceurpages import histogram, snapshot, text_of, volume_pages, write_result  # noqa: E402
from timestamps import NO_YEAR, file_years  # noqa: E402

SOURCES = [
    "pubdate",
    "submitted",
    "browser",
    "orig",
    "oldest",
    "index",
    "pubyear",
    "event",
    "title",
    "neighbours",
]
NEIGHBOURS = 25
YEAR4 = re.compile(r"(?<!\d)(\d{4})(?!\d)")
YEAR_IN_TEXT = re.compile(r"(?<!\d)(19[89]\d|20[0-3]\d)(?!\d)")
YEAR2 = re.compile(r"['’`](\d{2})(?!\d)")
DATE_TOKEN = r"[0-9]{1,4}[-./ ][0-9A-Za-z]{1,9}[-./ ,]{1,2}[0-9]{2,4}|[A-Z][a-z]+\.? [0-9]{1,2},? [0-9]{4}"
SUBMITTED_BEFORE = re.compile(r"(" + DATE_TOKEN + r")\s*:?\s*submitted by", re.I)
SUBMITTED_AFTER = re.compile(r"submitted by[^<]{0,120}?,\s*(" + DATE_TOKEN + r")", re.I)


def mark(html: str, name: str) -> Optional[str]:
    """
    get the text of the first element with the given CEUR class

    Args:
        html: the page
        name: the class, e.g. CEURPUBDATE

    Returns:
        Optional[str]: the text or None if there is no such mark
    """
    text = None
    match = re.search(r'class="' + name + r'"[^>]*>(.*?)</', html, re.S)
    if match:
        text = text_of(match.group(1))
    return text


def year4(text: Optional[str]) -> Optional[int]:
    """
    get the first four digit number of the given text as is

    Args:
        text: the text

    Returns:
        Optional[int]: the number or None
    """
    year = None
    if text:
        match = YEAR4.search(text)
        if match:
            year = int(match.group(1))
    return year


def text_year(text: Optional[str]) -> Optional[int]:
    """
    get the year named in an acronym or title, four digits or 'NN

    Args:
        text: the acronym or title

    Returns:
        Optional[int]: the year or None
    """
    year = None
    if text:
        match = YEAR_IN_TEXT.search(text)
        if match:
            year = int(match.group(1))
        else:
            match2 = YEAR2.search(text)
            if match2:
                two = int(match2.group(1))
                year = 1900 + two if two >= 80 else 2000 + two
    return year


def submitted_year(html: str) -> Optional[int]:
    """
    get the year of the date of the submitted by line

    Args:
        html: the page

    Returns:
        Optional[int]: the year or None
    """
    match = SUBMITTED_BEFORE.search(html) or SUBMITTED_AFTER.search(html)
    year = year4(match.group(1)) if match else None
    return year


def browser_years(path: str) -> Dict[int, Optional[int]]:
    """
    get the publication year per volume of the volume browser data

    Args:
        path: the volumes.json of the volume browser

    Returns:
        Dict[int, Optional[int]]: year per volume number
    """
    with open(path, encoding="utf-8") as json_file:
        records = json.load(json_file)
    years = {}
    for record in records:
        years[record["number"]] = year4(record.get("published") or record.get("pubDate"))
    return years


def browser_texts(path: str) -> Dict[int, Dict[str, Optional[str]]]:
    """
    get acronym and title per volume of the volume browser data

    Args:
        path: the volumes.json of the volume browser

    Returns:
        Dict[int, Dict[str, Optional[str]]]: acronym and title per volume number
    """
    with open(path, encoding="utf-8") as json_file:
        records = json.load(json_file)
    texts = {record["number"]: {"acronym": record.get("acronym"), "title": record.get("title")} for record in records}
    return texts


def event_years(log_path: str) -> Dict[int, Optional[int]]:
    """
    get the event year per volume from the Round 0 log

    Args:
        log_path: the complete.jsonl of Round 0

    Returns:
        Dict[int, Optional[int]]: the tree year where it is the event year, else None
    """
    years = {}
    with open(log_path, encoding="utf-8") as log_file:
        for line in log_file:
            row = json.loads(line)
            inferred = NO_YEAR in (row.get("message") or "")
            years[row["volume"]] = None if inferred else year4(row.get("tree_year"))
    return years


def vote(years: Dict[str, Optional[int]]) -> Dict:
    """
    count the votes of one volume

    Args:
        years: year per source

    Returns:
        Dict: number of votes, groups, size of the largest group and the winner if unique
    """
    given = [year for year in years.values() if year is not None]
    groups = histogram(given)
    sizes = sorted(groups.values(), reverse=True)
    largest = sizes[0] if sizes else 0
    unique = len(sizes) == 1 or (len(sizes) > 1 and sizes[0] > sizes[1])
    winner = int(next(iter(groups))) if sizes and unique else None
    result = {
        "votes": len(given),
        "largest": largest,
        "winner": winner,
        "absolute": largest * 2 > len(given),
        "groups": groups,
    }
    return result


def main() -> None:
    """
    collect the votes, count them and write the result
    """
    parser = argparse.ArgumentParser(description="votes of ten sources on the year of each volume")
    parser.add_argument("--www", required=True, help="www directory of the copy, only read")
    parser.add_argument("--log", required=True, help="Round 0 log, complete.jsonl, defines the volumes")
    parser.add_argument("--browser", required=True, help="volumes.json of the volume browser")
    parser.add_argument("--out", required=True, help="result json")
    parser.add_argument("--snapshot", help="commit of the copy the www directory is at")
    args = parser.parse_args()
    events = event_years(args.log)
    browser = browser_years(args.browser)
    texts = browser_texts(args.browser)
    rows: List[Dict] = []
    for number, html in volume_pages(args.www):
        if number not in events:
            continue
        files = file_years(args.www, number)
        acronym = mark(html, "CEURVOLACRONYM") or texts.get(number, {}).get("acronym")
        title = mark(html, "CEURVOLTITLE") or texts.get(number, {}).get("title")
        years = {
            "pubdate": year4(mark(html, "CEURPUBDATE")),
            "submitted": submitted_year(html),
            "browser": browser.get(number),
            "orig": files["orig"],
            "oldest": files["oldest"],
            "index": files["index"],
            "pubyear": year4(mark(html, "CEURPUBYEAR")),
            "event": events[number],
            "title": text_year(acronym) or text_year(title),
            "neighbours": None,
        }
        rows.append({"volume": number, "years": years})
    pubdates = {row["volume"]: row["years"]["pubdate"] for row in rows}
    numbers = sorted(pubdates)
    for index, row in enumerate(rows):
        around = numbers[max(0, index - NEIGHBOURS) : index] + numbers[index + 1 : index + 1 + NEIGHBOURS]
        values = [pubdates[n] for n in around if pubdates[n] is not None]
        row["years"]["neighbours"] = int(statistics.median_low(values)) if values else None
        row.update(vote(row["years"]))
    per_source = {}
    for source in SOURCES:
        given = [row for row in rows if row["years"][source] is not None]
        with_winner = [row for row in given if row["winner"] is not None]
        with_pubdate = [row for row in given if row["years"]["pubdate"] is not None]
        per_source[source] = {
            "votes": len(given),
            "compared_with_majority": len(with_winner),
            "agree_with_majority": sum(1 for row in with_winner if row["years"][source] == row["winner"]),
            "compared_with_pubdate": len(with_pubdate),
            "agree_with_pubdate": sum(1 for row in with_pubdate if row["years"][source] == row["years"]["pubdate"]),
        }
    no_majority = [
        {"volume": row["volume"], "years": {k: v for k, v in row["years"].items() if v is not None}}
        for row in rows
        if row["winner"] is None
    ]
    result = {
        "snapshot": {"commit": args.snapshot, **snapshot(args.www)},
        "sources": SOURCES,
        "volumes": len(rows),
        "per_volume_votes": histogram([row["votes"] for row in rows], key=lambda v: f"{v:02d}"),
        "per_volume_largest": histogram([row["largest"] for row in rows], key=lambda v: f"{v:02d}"),
        "unique_plurality": sum(1 for row in rows if row["winner"] is not None),
        "absolute_majority": sum(1 for row in rows if row["absolute"]),
        "per_source": per_source,
        "without_majority": no_majority,
        "rows": [{"volume": row["volume"], "winner": row["winner"], "votes": row["votes"], "largest": row["largest"], "years": row["years"]} for row in rows],
    }
    write_result(result, args.out)

if __name__ == "__main__":
    main()
