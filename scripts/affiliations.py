"""
Created on 2026-11-10

@author: wf

measure how the volume pages write the affiliations of the editors, the
counting rules of the comment of 2026-11-07 on semantify #67 written again,
see SemanticLongTail #1 and #2

usage: python3 -I affiliations.py <www> [result.json]
"""

import os
import re
import sys

# python3 -I does not put the script directory on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ceurpages import histogram, snapshot, volume_pages, write_result  # noqa: E402

EDITOR_PATTERN = re.compile(r"<span\b[^>]*class\s*=\s*[\"']?CEURVOLEDITOR[\"']?[^>]*>.*?</span>", re.S | re.I)
# what follows an editor span up to the line break, the next editor or the end of the heading
AFTER_PATTERN = re.compile(r"(.*?)(?:<br|<span\b[^>]*CEURVOLEDITOR|</h\d|</p|</div|$)", re.S | re.I)
HR_PATTERN = re.compile(r"<hr\b", re.I)
LINE_SPLIT = re.compile(r"<br\s*/?>|</p>|</div>|\n", re.I)
TAG_PATTERN = re.compile(r"<[^>]+>")


# footnote symbols the editors use after a name and in front of an affiliation line
SYMBOLS = "*#+%^$°§†‡"
SYMBOL_PATTERN = re.compile(r"^[" + re.escape(SYMBOLS) + r"\s,]+$")


def marker_kind(after: str) -> str:
    """
    classify what follows an editor name

    Args:
        after: the html following the editor span

    Returns:
        str: asterisks (only *), symbols (other footnote symbols), sup, numbers
            (plain numbers without sup), other text, or none
    """
    if re.search(r"<sup\b", after, re.I):
        kind = "sup"
    else:
        text = TAG_PATTERN.sub("", after).replace("&nbsp;", " ").strip(" ,;")
        if not text:
            kind = "none"
        elif re.fullmatch(r"\*+", text):
            kind = "asterisks"
        elif SYMBOL_PATTERN.match(text):
            kind = "symbols"
        elif re.fullmatch(r"[\(\[]?[0-9][0-9,\s]*[\)\]]?", text):
            kind = "numbers"
        else:
            kind = "other"
    return kind


def block_lines(block: str) -> list:
    """
    get the affiliation lines of the block after the editors

    Args:
        block: the html between the end of the editor heading and the hr

    Returns:
        list: the kinds of the lines, asterisk (starting with *), symbol (starting with
            another footnote symbol), number (starting with a plain number) or sup, in order
    """
    kinds = []
    for line in LINE_SPLIT.split(block):
        text = TAG_PATTERN.sub("", line).replace("&nbsp;", " ").strip()
        if not text:
            continue
        if re.search(r"^\s*<sup\b", line, re.I) or re.search(r"<sup\b[^>]*>\s*[0-9,\s]+</sup>", line, re.I):
            kinds.append("sup")
        elif text.startswith("*"):
            kinds.append("asterisk")
        elif text[0] in SYMBOLS:
            kinds.append("symbol")
        elif re.match(r"[\(\[]?[0-9]+[\)\].]?\s", text):
            kinds.append("number")
    return kinds


def measure(www: str) -> dict:
    """
    measure the affiliation conventions of all volumes

    Args:
        www: the directory holding Vol-N/index.html

    Returns:
        dict: the measurement
    """
    volumes = 0
    volumes_with_editors = 0
    marker_kinds = []
    block_kinds = []
    agreement = 0
    agreement_by_kind = {"symbols": 0, "sup": 0, "numbers": 0}
    lines_per_block = []
    for number, html in volume_pages(www):
        volumes += 1
        editors = list(EDITOR_PATTERN.finditer(html))
        if not editors:
            continue
        volumes_with_editors += 1
        kinds = set()
        for match in editors:
            after = AFTER_PATTERN.match(html, match.end()).group(1)
            kinds.add(marker_kind(after))
        # the volume takes the convention of its editors, in this order of precedence
        order = ("asterisks", "symbols", "sup", "numbers", "other", "none")
        marker = next((kind for kind in order if kind in kinds), "none")
        marker_kinds.append(marker)
        end = editors[-1].end()
        hr = HR_PATTERN.search(html, end)
        block = html[end : hr.start()] if hr else html[end : end + 4000]
        lines = block_lines(block)
        if "asterisk" in lines or "symbol" in lines:
            block_kind = "symbol lines"
        elif "sup" in lines:
            block_kind = "sup lines"
        elif "number" in lines:
            block_kind = "number lines"
        else:
            block_kind = "none"
        block_kinds.append(block_kind)
        if lines:
            lines_per_block.append(len(lines))
        if marker in ("asterisks", "symbols") and block_kind == "symbol lines":
            agreement += 1
            agreement_by_kind["symbols"] += 1
        elif marker == "sup" and block_kind == "sup lines":
            agreement += 1
            agreement_by_kind["sup"] += 1
        elif marker == "numbers" and block_kind == "number lines":
            agreement += 1
            agreement_by_kind["numbers"] += 1
    result = {
        "snapshot": snapshot(www),
        "volumes": volumes,
        "volumes_with_editors": volumes_with_editors,
        "marker_after_name": histogram(marker_kinds),
        "block_after_editors": histogram(block_kinds),
        "agreement": agreement,
        "agreement_by_kind": agreement_by_kind,
        "lines_per_block": histogram(lines_per_block, key=lambda n: n if n < 10 else "10+"),
    }
    return result


if __name__ == "__main__":
    www_dir = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    write_result(measure(www_dir), out_path)
