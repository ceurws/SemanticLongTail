"""
Created on 2026-11-22

@author: wf

template versions of the volume pages, see SemanticLongTail #6; standard
library only, run with python3 -I on a copy of the volume pages

criteria, in this order:
    C1  the declared version, the comment CEURVERSION=... of the page
    C2  for a page without a declared version: the structural signature of
        the page, its markup layer, doctype, RDFa prefixes, the CEUR classes
        of the page header and the CEURLANG, viewport and lang markers;
        a C2 version is dated by the volume of its first use

markup layer:
    plain  no CEUR class and no RDFa attribute
    ceur   CEUR classes, no RDFa attribute
    rdfa   RDFa attributes typeof or property

the date of a volume is its CEURPUBDATE where it parses to a day, else the
year of publication given by yearvotes.py
"""

import argparse
import datetime
import json
import os
import re
import sys
from typing import Dict, List, Optional

# python3 -I does not put the script directory on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ceurpages import histogram, snapshot, text_of, volume_pages, write_result  # noqa: E402

CLASS_ATTR = re.compile(r"""class\s*=\s*["']([^"']*)["']""", re.I)
COMMENT_MARK = re.compile(r"<!--\s*(CEUR[A-Z]+)\s*=\s*([^\s>]*?)\s*-->", re.I)
DOCTYPE = re.compile(r"<!DOCTYPE\s+([^>]*)>", re.I)
HTML_TAG = re.compile(r"<html\b([^>]*)>", re.I | re.S)
PREFIX_ATTR = re.compile(r"""\bprefix\s*=\s*["']([^"']*)["']""", re.I)
XMLNS_ATTR = re.compile(r"""\bxmlns:([A-Za-z_][\w.-]*)\s*=""")
RDFA_ATTR =re.compile(r"""\b(typeof|property)\s*=\s*["']([^"']*)["']""", re.I)
VIEWPORT = re.compile(r"""<meta[^>]*name\s*=\s*["']viewport["']""", re.I)
PUBDATE = re.compile(r"""class\s*=\s*["']CEURPUBDATE["'][^>]*>(.*?)</""", re.I | re.S)
# classes of the page header: title, volume, URN, date, license, event;
# the classes of the table of contents depend on the editors, not the template
HEADER_CLASSES = {
    "CEURVOLNR",
    "CEURURN",
    "CEURVOLACRONYM",
    "CEURVOLTITLE",
    "CEURFULLTITLE",
    "CEURCOLOCATED",
    "CEURLOCTIME",
    "CEURPUBYEAR",
    "CEURPUBDATE",
    "CEURLIC",
    "CEURVOLEDITOR",
    "CEURSUBMITTEDBY",
    "CEURTOC",
}
DATE_FORMATS = ["%Y-%m-%d", "%d-%b-%Y", "%d-%B-%Y", "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%d.%m.%Y"]


def parse_day(text: Optional[str]) -> Optional[str]:
    """
    get the ISO day of the given date text

    Args:
        text: the text of the CEURPUBDATE mark

    Returns:
        Optional[str]: yyyy-mm-dd or None if the text is no day
    """
    day = None
    if text:
        for date_format in DATE_FORMATS:
            try:
                day = datetime.datetime.strptime(text.strip(), date_format).date().isoformat()
                break
            except ValueError:
                pass
    return day


def doctype_of(html: str) -> str:
    """
    get the normalized doctype of the page

    Args:
        html: the page

    Returns:
        str: the doctype in lower case with whitespace collapsed, or none
    """
    match = DOCTYPE.search(html)
    doctype = "none"
    if match:
        doctype = re.sub(r"\s+", " ", match.group(1).lower()).strip()
        doctype = re.sub(r'\s*"http[^"]*"', "", doctype)
    return doctype


def features(html: str) -> Dict:
    """
    get the structural features of the given volume page

    Args:
        html: the page

    Returns:
        Dict: classes, comment marks, RDFa, doctype and markers
    """
    classes = set()
    for match in CLASS_ATTR.finditer(html):
        classes.update(token for token in match.group(1).split() if token.upper().startswith("CEUR"))
    marks = {}
    for match in COMMENT_MARK.finditer(html):
        marks.setdefault(match.group(1).upper(), match.group(2))
    prefixes = set()
    for match in PREFIX_ATTR.finditer(html):
        prefixes.update(token[:-1] for token in match.group(1).split() if token.endswith(":"))
    # RDFa 1.0 declares its prefixes as xmlns:name
    prefixes.update(match.group(1) for match in XMLNS_ATTR.finditer(html))
    rdfa_used = set()
    for match in RDFA_ATTR.finditer(html):
        rdfa_used.update(token.split(":", 1)[0] for token in match.group(2).split() if ":" in token)
    html_tag = HTML_TAG.search(html)
    html_attrs = html_tag.group(1) if html_tag else ""
    has_rdfa = bool(RDFA_ATTR.search(html))
    layer = "rdfa" if has_rdfa else ("ceur" if classes else "plain")
    pubdate = PUBDATE.search(html)
    result = {
        "layer": layer,
        "version": marks.get("CEURVERSION"),
        "doctype": doctype_of(html),
        "prefixes": sorted(prefixes),
        "rdfa_vocabularies": sorted(rdfa_used),
        "classes": sorted(classes),
        "header_classes": sorted(classes & HEADER_CLASSES),
        "comment_marks": sorted(marks),
        "viewport": bool(VIEWPORT.search(html)),
        "lang": bool(re.search(r"\blang\s*=", html_attrs, re.I)),
        "pubdate": text_of(pubdate.group(1)) if pubdate else None,
    }
    return result


COPYRIGHT = re.compile(r"((?:copyright\s*)?(?:&copy;|©|\(c\))[^<]{0,40}?\d{4}.{0,400}?owners\.?(?:\s*this volume is published by its editors\.?)?)", re.I | re.S)
GENERATOR = re.compile(r"""<meta[^>]*name\s*=\s*["']?generator["']?[^>]*content\s*=\s*["']([^"']*)""", re.I)
DESCRIPTION_CEUR = re.compile(r"""<meta[^>]*name\s*=\s*["']?descr?ipt?ion["']?[^>]*content\s*=\s*["'][^"']*CEUR Workshop Proceedings""", re.I)
SUBMITTED_DATED = re.compile(r"submitted\s+by[^<]{0,160}?,\s*(?:\d|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", re.I)
# the boilerplate of the volume pages before the CEUR classes, from a sample of
# ten volumes, Vol-1 to Vol-558; each is a candidate element of a pre CEUR template
BOILERPLATE = {
    "logo": re.compile(r"CEUR-WS-logo", re.I),
    "css": re.compile(r"ceur-ws\.css", re.I),
    "header_table": re.compile(r"""<table[^>]*cellspacing\s*=\s*["']?5["']?[^>]*>""", re.I),
    "font_arial": re.compile(r"""<font[^>]*face\s*=\s*["']?arial""", re.I),
    "font_blue_5": re.compile(r"""<font[^>]*#0f0ff0""", re.I),
    "font_grey_-2": re.compile(r"""<font(?=[^>]*#777777)(?=[^>]*size\s*=\s*["']?-2)[^>]*>""", re.I),
    "font_grey_-1": re.compile(r"""<font(?=[^>]*#777777)(?=[^>]*size\s*=\s*["']?-1)[^>]*>""", re.I),
    "meta_description_ceur": DESCRIPTION_CEUR,
    "meta_charset": re.compile(r"""<meta[^>]*charset""", re.I),
    "submitted_by": re.compile(r"submitted\s+by", re.I),
    "submitted_by_dated": SUBMITTED_DATED,
    "copyright_word": re.compile(r"copyright\s*(?:&copy;|©)", re.I),
    "published_by_editors": re.compile(r"published\s+by\s+its\s+editors", re.I),
}


def copyright_variant(html: str) -> Optional[str]:
    """
    get the copyright line of the page with years and whitespace normalized

    Args:
        html: the page

    Returns:
        Optional[str]: the normalized copyright line or None
    """
    variant = None
    match = COPYRIGHT.search(html)
    if match:
        text = text_of(match.group(1)).lower().replace("©", "&copy;")
        variant = re.sub(r"\b(19|20)\d\d\b", "YYYY", text)
    return variant


def boilerplate(html: str) -> Dict:
    """
    get the boilerplate elements of a page before the CEUR classes

    Args:
        html: the page

    Returns:
        Dict: the elements found, the copyright variant and the generator
    """
    generator = GENERATOR.search(html)
    result = {
        "elements": sorted(name for name, pattern in BOILERPLATE.items() if pattern.search(html)),
        "copyright": copyright_variant(html),
        "generator": generator.group(1).split("/")[0].split(" ")[0] if generator else None,
    }
    return result


def signature(feature: Dict) -> str:
    """
    get the structural signature of criterion C2

    Args:
        feature: the features of a page

    Returns:
        str: the signature as one line
    """
    parts = [
        feature["layer"],
        "doctype=" + feature["doctype"],
        "prefixes=" + ",".join(feature["prefixes"]),
        "header=" + ",".join(feature["header_classes"]),
        "author=" + ",".join(c for c in ("CEURAUTHOR", "CEURAUTHORS") if c in feature["classes"]),
        "marks=" + ",".join(m for m in feature["comment_marks"] if m != "CEURVERSION"),
        "viewport" if feature["viewport"] else "",
        "lang" if feature["lang"] else "",
    ]
    text = " ".join(part for part in parts if part)
    return text


def template_features(feature: Dict) -> List[str]:
    """
    get the features that count as template elements for the change list

    Args:
        feature: the features of a page

    Returns:
        List[str]: the template elements of the page
    """
    elements = [f"layer:{feature['layer']}", f"doctype:{feature['doctype']}"]
    elements += [f"class:{c}" for c in feature["header_classes"]]
    elements += [f"class:{c}" for c in ("CEURAUTHOR", "CEURAUTHORS") if c in feature["classes"]]
    elements += [f"prefix:{p}" for p in feature["prefixes"]]
    elements += [f"vocabulary:{v}" for v in feature["rdfa_vocabularies"]]
    elements += [f"comment:{m}" for m in feature["comment_marks"]]
    if feature["viewport"]:
        elements.append("meta:viewport")
    if feature["lang"]:
        elements.append("html:lang")
    return elements


def year_of_publication(path: str) -> Dict[int, Optional[int]]:
    """
    get the year of publication per volume from the result of yearvotes.py

    Args:
        path: yearvotes.json

    Returns:
        Dict[int, Optional[int]]: volume to the year of the plurality, else CEURPUBDATE
    """
    with open(path, encoding="utf-8") as json_file:
        votes = json.load(json_file)
    years = {row["volume"]: row["winner"] or row["years"].get("pubdate") for row in votes["rows"]}
    return years


def group(rows: List[Dict], key: str) -> List[Dict]:
    """
    group the rows by the given key in the order of their first volume

    Args:
        rows: the per volume rows
        key: version or signature

    Returns:
        List[Dict]: per group the first and last volume, dates, count and
        the template elements present in at least half of its volumes
    """
    groups: Dict[str, List[Dict]] = {}
    for row in rows:
        groups.setdefault(row[key], []).append(row)
    result = []
    for value, members in groups.items():
        counts = histogram([e for m in members for e in m["elements"]])
        majority = sorted(e for e, n in counts.items() if 2 * n >= len(members))
        dates = [m["date"] for m in members if m["date"]]
        result.append(
            {
                key: value,
                "volumes": len(members),
                "first_volume": members[0]["volume"],
                "last_volume": members[-1]["volume"],
                "first_date": members[0]["date"],
                "last_date": members[-1]["date"],
                "min_date": min(dates) if dates else None,
                "max_date": max(dates) if dates else None,
                "layers": histogram([m["layer"] for m in members]),
                "elements": majority,
            }
        )
    result.sort(key=lambda g: g["first_volume"])
    previous: List[str] = []
    for entry in result:
        entry["added"] = sorted(set(entry["elements"]) - set(previous))
        entry["removed"] = sorted(set(previous) - set(entry["elements"]))
        previous = entry["elements"]
    return result


def first_uses(rows: List[Dict]) -> List[Dict]:
    """
    get the first use of every template element

    Args:
        rows: the per volume rows

    Returns:
        List[Dict]: element, first and last volume, date of first use, count
    """
    uses: Dict[str, Dict] = {}
    for row in rows:
        for element in row["elements"]:
            use = uses.setdefault(element, {"element": element, "first_volume": row["volume"], "date": row["date"], "volumes": 0})
            use["volumes"] += 1
            use["last_volume"] = row["volume"]
    result = sorted(uses.values(), key=lambda u: (u["first_volume"], u["element"]))
    return result


def pre_ceur(args, years: Dict[int, Optional[int]]) -> None:
    """
    measure the boilerplate of the volumes before the CEUR classes and of the
    plain volumes after them and write the result

    Args:
        args: the command line arguments
        years: year of publication per volume
    """
    rows: List[Dict] = []
    for number, html in volume_pages(args.www):
        if number > args.last:
            continue
        feature = features(html)
        if number >= args.boundary and feature["layer"] != "plain":
            continue
        plate = boilerplate(html)
        year = years.get(number)
        elements = [f"doctype:{feature['doctype']}", f"layer:{feature['layer']}"] + plate["elements"]
        rows.append(
            {
                "volume": number,
                "date": str(year) if year else None,
                "layer": feature["layer"],
                "signature": " ".join(elements),
                "elements": elements,
                "copyright": plate["copyright"],
                "generator": plate["generator"],
            }
        )
    signatures = group(rows, "signature")
    result = {
        "snapshot": {"commit": args.snapshot, "last_volume": args.last, "boundary": args.boundary, **snapshot(args.www)},
        "criterion": "volumes before the boundary and plain volumes after it: signature of doctype, layer and the boilerplate elements " + ", ".join(BOILERPLATE),
        "volumes": len(rows),
        "after_boundary": [row["volume"] for row in rows if row["volume"] >= args.boundary],
        "layers": histogram([row["layer"] for row in rows]),
        "elements": histogram([e for row in rows for e in row["elements"]]),
        "first_uses": first_uses(rows),
        "copyright_variants": histogram([row["copyright"] for row in rows]),
        "generators": histogram([row["generator"] for row in rows]),
        "signatures": len(signatures),
        "signatures_2_or_more_volumes": sum(1 for g in signatures if g["volumes"] >= 2),
        "versions": signatures,
        "rows": [{k: row[k] for k in ("volume", "date", "layer", "signature", "copyright", "generator")} for row in rows],
    }
    write_result(result, args.pre_out)


def main() -> None:
    """
    measure the template version of every volume page and write the result
    """
    parser = argparse.ArgumentParser(description="template versions of the volume pages")
    parser.add_argument("--www", required=True, help="www directory of the copy, only read")
    parser.add_argument("--years", required=True, help="yearvotes.json, year of publication per volume")
    parser.add_argument("--last", type=int, required=True, help="last volume of the snapshot")
    parser.add_argument("--out", help="result json of all volumes")
    parser.add_argument("--snapshot", help="commit of the copy the www directory is at")
    parser.add_argument("--boundary", type=int, help="first volume with CEUR classes; with --pre-out only the volumes before it and the plain ones after it")
    parser.add_argument("--pre-out", help="result json of the volumes before the boundary")
    args = parser.parse_args()
    years = year_of_publication(args.years)
    if args.pre_out:
        pre_ceur(args, years)
        return
    rows: List[Dict] = []
    for number, html in volume_pages(args.www):
        if number > args.last:
            continue
        feature = features(html)
        day = parse_day(feature["pubdate"])
        year = years.get(number)
        date = day or (str(year) if year else None)
        declared = feature["version"]
        row = {
            "volume": number,
            "date": date,
            "date_source": "CEURPUBDATE" if day else ("year of publication" if year else None),
            "layer": feature["layer"],
            "criterion": "C1" if declared is not None else "C2",
            "version": declared,
            "signature": signature(feature),
            "elements": template_features(feature),
        }
        rows.append(row)
    declared_rows = [row for row in rows if row["criterion"] == "C1"]
    undeclared_rows = [row for row in rows if row["criterion"] == "C2"]
    c1 = group(declared_rows, "version")
    c2 = group(undeclared_rows, "signature")
    well_formed = [g for g in c1 if parse_day(g["version"])]
    # declared versions with the same template elements in the majority of their volumes
    structures: Dict[tuple, List[Dict]] = {}
    for entry in c1:
        structures.setdefault(tuple(entry["elements"]), []).append(entry)
    c1_structures = [
        {
            "versions": [e["version"] for e in members],
            "volumes": sum(e["volumes"] for e in members),
            "first_volume": min(e["first_volume"] for e in members),
            "elements": list(elements),
        }
        for elements, members in structures.items()
    ]
    result = {
        "snapshot": {"commit": args.snapshot, "last_volume": args.last, **snapshot(args.www)},
        "criteria": {
            "C1": "declared version, comment CEURVERSION=... of the page",
            "C2": "no declared version: signature of layer, doctype, RDFa prefixes, header classes, author class, comment marks, viewport and lang, dated by its first volume",
        },
        "volumes": len(rows),
        "layers": histogram([row["layer"] for row in rows]),
        "criterion": histogram([row["criterion"] for row in rows]),
        "counts": {
            "published": 33,
            "C1_values": len(c1),
            "C1_valid_dates": len(well_formed),
            "C1_structures": len(c1_structures),
            "C1_volumes": len(declared_rows),
            "C2_signatures": len(c2),
            "C2_signatures_2_or_more_volumes": sum(1 for g in c2 if g["volumes"] >= 2),
            "C2_volumes": len(undeclared_rows),
        },
        "first_layer_use": {layer: next((row["volume"] for row in rows if row["layer"] == layer), None) for layer in ("plain", "ceur", "rdfa")},
        "first_uses": first_uses(rows),
        "C1_versions": c1,
        "C1_structures": c1_structures,
        "C2_versions": c2,
        "rows": [{k: row[k] for k in ("volume", "date", "date_source", "layer", "criterion", "version", "signature")} for row in rows],
    }
    write_result(result, args.out)


if __name__ == "__main__":
    main()
