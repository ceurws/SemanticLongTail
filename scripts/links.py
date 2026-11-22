"""
Created on 2026-11-22

@author: wf

the links of the volume pages, see SemanticLongTail #7; standard library
only, run with python3 -I on a copy of the volume pages; offline, no request
to any host

a link is the href of an a element; its kind:
    anchor    empty or starting with #
    volume    relative, within the volume directory
    ceur      relative outside the volume directory, or absolute on ceur-ws.org
    external  absolute http or https on another host
    mailto    mailto:
    other     any other scheme
"""

import argparse
import json
import os
import sys
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ceurpages import histogram, snapshot, volume_pages, write_result  # noqa: E402

CEUR_HOSTS = {"ceur-ws.org", "www.ceur-ws.org", "sunsite.informatik.rwth-aachen.de"}
KINDS = ["anchor", "volume", "ceur", "external", "mailto", "other"]


class HrefParser(HTMLParser):
    """
    collect the href values of the a elements
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value is not None:
                    self.hrefs.append(value.strip())


def hrefs_of(html: str) -> List[str]:
    """
    get the hrefs of the a elements of the given page

    Args:
        html: the page

    Returns:
        List[str]: the href values in page order
    """
    parser = HrefParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    return parser.hrefs


def kind_of(href: str) -> str:
    """
    get the kind of the given href

    Args:
        href: the href value

    Returns:
        str: one of KINDS
    """
    if href == "" or href.startswith("#"):
        return "anchor"
    lower = href.lower()
    if lower.startswith("mailto:"):
        return "mailto"
    parts = urlsplit(href)
    if parts.scheme and parts.scheme.lower() not in ("http", "https"):
        return "other"
    if parts.scheme or href.startswith("//"):
        host = (parts.hostname or "").lower()
        return "ceur" if host in CEUR_HOSTS else "external"
    if href.startswith("/") or href.startswith(".."):
        return "ceur"
    return "volume"


def host_of(href: str) -> str:
    """
    get the lower case host of an absolute href

    Args:
        href: the href value

    Returns:
        str: the host
    """
    host = (urlsplit(href).hostname or "").lower()
    return host


def year_of_publication(path: Optional[str]) -> Dict[int, Optional[int]]:
    """
    get the year of publication per volume from the result of yearvotes.py

    Args:
        path: yearvotes.json or None

    Returns:
        Dict[int, Optional[int]]: volume to the year of the plurality, else CEURPUBDATE
    """
    years: Dict[int, Optional[int]] = {}
    if path:
        with open(path, encoding="utf-8") as json_file:
            votes = json.load(json_file)
        years = {row["volume"]: row["winner"] or row["years"].get("pubdate") for row in votes["rows"]}
    return years


def measure(args) -> Dict:
    """
    count the links of the volume pages

    Args:
        args: the command line arguments

    Returns:
        Dict: the result
    """
    years = year_of_publication(args.years)
    rows = []
    distinct = {kind: set() for kind in KINDS}
    hosts: List[str] = []
    per_year: Dict[str, Dict] = {}
    extensions: List[str] = []
    for volume, html in volume_pages(args.www):
        if args.last and volume > args.last:
            continue
        hrefs = hrefs_of(html)
        counts = {kind: 0 for kind in KINDS}
        volume_hosts = set()
        for href in hrefs:
            kind = kind_of(href)
            counts[kind] += 1
            distinct[kind].add(href if kind != "volume" else f"Vol-{volume}/{href}")
            if kind == "external":
                host = host_of(href)
                hosts.append(host)
                volume_hosts.add(host)
            if kind == "volume":
                path = urlsplit(href).path
                extension = os.path.splitext(path)[1].lower() or "(none)"
                extensions.append(extension)
        year = years.get(volume)
        rows.append({"volume": volume, "year": year, "links": len(hrefs), **counts, "external_hosts": len(volume_hosts)})
        bucket = per_year.setdefault(str(year), {"volumes": 0, "links": 0, **{kind: 0 for kind in KINDS}, "hosts": set()})
        bucket["volumes"] += 1
        bucket["links"] += len(hrefs)
        for kind in KINDS:
            bucket[kind] += counts[kind]
        bucket["hosts"] |= volume_hosts
    for bucket in per_year.values():
        bucket["external_hosts"] = len(bucket.pop("hosts"))
    host_counts = histogram(hosts)
    result = {
        "snapshot": {**snapshot(args.www), "commit": args.snapshot},
        "criterion": __doc__.strip().split("\n\n", 1)[1],
        "counts": {
            "volumes": len(rows),
            "volumes_without_links": sum(1 for row in rows if row["links"] == 0),
            "links": sum(row["links"] for row in rows),
            **{kind: sum(row[kind] for row in rows) for kind in KINDS},
            "distinct": {kind: len(values) for kind, values in distinct.items()},
            "external_hosts": len(host_counts),
        },
        "volume_link_extensions": histogram(extensions),
        "per_year": dict(sorted(per_year.items())),
        "top_hosts": dict(list(host_counts.items())[: args.top]),
        "rows": rows,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="the links of the volume pages, offline")
    parser.add_argument("--www", required=True, help="directory holding Vol-N/index.html")
    parser.add_argument("--years", help="yearvotes.json for the year of publication")
    parser.add_argument("--last", type=int, help="last volume to include")
    parser.add_argument("--snapshot", help="commit of the copy")
    parser.add_argument("--top", type=int, default=50, help="number of hosts listed")
    parser.add_argument("--out", help="result JSON, default stdout")
    args = parser.parse_args()
    write_result(measure(args), args.out)


if __name__ == "__main__":
    main()
