"""
Created on 2026-11-10

@author: wf

measure the CEURSESSION headings of all volume pages, the counting rules of
semantify discussion 74 of 2026-11-06 written again, see SemanticLongTail #1

usage: python3 -I sessions.py <www> [result.json]
"""

import os
import re
import sys

# python3 -I does not put the script directory on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ceurpages import histogram, snapshot, text_of, volume_pages, write_result  # noqa: E402

# a CEURSESSION element: the tag, its content up to the closing tag
SESSION_PATTERN = re.compile(
    r"<(h\d|li|p|div|span|b|strong|td|dt)\b[^>]*class\s*=\s*[\"']?CEURSESSION[\"']?[^>]*>(.*?)</\1>",
    re.S | re.I,
)
# the element that holds a CEURSESSION span, e.g. <h3><span class="CEURSESSION">
ENCLOSING_PATTERN = re.compile(r"<(h\d|li|p|td|dt|b|strong|div)\b[^>]*>\s*$", re.I)
MARK_PATTERN = re.compile(r"class\s*=\s*[\"']?(CEURSESSION|CEURTITLE)[\"']?", re.I)


def heading_element(html: str, match: re.Match) -> str:
    """
    get the element that holds the session mark: the marked element itself,
    or for a marked span the element the span stands in

    Args:
        html: the page
        match: the match of SESSION_PATTERN

    Returns:
        str: the lower case tag name
    """
    tag = match.group(1).lower()
    if tag == "span":
        before = html[max(0, match.start() - 200) : match.start()]
        enclosing = ENCLOSING_PATTERN.search(before)
        if enclosing:
            tag = enclosing.group(1).lower()
    return tag

KIND_WORDS = [
    "extended abstract",
    "work in progress",
    "late breaking",
    "short",
    "invited",
    "regular",
    "poster",
    "keynote",
    "full",
    "doctoral",
    "long",
    "demo",
    "abstract",
    "position",
    "preface",
    "tutorial",
    "phd",
    "student",
    "panel",
]

def kind_pattern(word: str) -> re.Pattern:
    """
    get the pattern of a kind word: plural allowed, a space in the word may be a hyphen,
    abstract does not match inside extended abstract

    Args:
        word: the kind word

    Returns:
        re.Pattern: the pattern
    """
    body = r"[\s-]+".join(re.escape(part) for part in word.split())
    prefix = r"(?<!extended )(?<!extended-)" if word == "abstract" else ""
    pattern = re.compile(prefix + r"\b" + body + r"s?\b", re.I)
    return pattern


KIND_PATTERNS = {word: kind_pattern(word) for word in KIND_WORDS}
SLOT_PATTERN = re.compile(
    r"\b(session|part|track|day|block|chapter|volume|section)\s*[:\-]?\s*([0-9]+|[IVX]+)\b|^\s*([0-9]+|[IVX]+)\s*[.:)-]",
    re.I,
)
ACRONYM_PATTERN = re.compile(r"\(([A-Z][A-Za-z0-9&+/-]*[A-Z0-9][A-Za-z0-9&+/-]*)(?:\s*['’]?\s*\d{2,4})?\)")
ORGANIZERS_PATTERN = re.compile(r"\b(org\.|organi[sz]ed by|organi[sz]ers?|chairs?:)", re.I)


def facets_of(text: str) -> str:
    """
    classify the heading text by the facets it carries

    Args:
        text: the heading text

    Returns:
        str: the facet combination, e.g. "slot+kind+theme"
    """
    facets = []
    rest = text
    if SLOT_PATTERN.search(rest):
        facets.append("slot")
        rest = SLOT_PATTERN.sub(" ", rest)
    if any(pattern.search(rest) for pattern in KIND_PATTERNS.values()):
        facets.append("kind")
        for pattern in KIND_PATTERNS.values():
            rest = pattern.sub(" ", rest)
    if ACRONYM_PATTERN.search(rest):
        facets.append("acronym")
        rest = ACRONYM_PATTERN.sub(" ", rest)
    if ORGANIZERS_PATTERN.search(rest):
        facets.append("organizers")
        rest = ORGANIZERS_PATTERN.split(rest)[0]
    rest = re.sub(r"[\s:;,.\-–—()\[\]]+", " ", rest).strip()
    # a theme needs a word, not only paper(s) or papers on
    if re.search(r"[A-Za-z]{3,}", re.sub(r"\b(papers?|talks?|on|of|and|the|session)\b", " ", rest, flags=re.I)):
        facets.append("theme")
    combination = "+".join(facets) if facets else "none"
    return combination


def measure(www: str) -> dict:
    """
    measure the sessions of all volumes

    Args:
        www: the directory holding Vol-N/index.html

    Returns:
        dict: the measurement
    """
    volumes = 0
    volumes_with_sessions = 0
    tag_sets = []
    sessions_per_volume = []
    heading_texts = []
    papers_per_heading = []
    pairs = 0
    pair_volumes = 0
    pair_volume_numbers = []
    kind_headings = {word: 0 for word in KIND_WORDS}
    kind_volumes = {word: 0 for word in KIND_WORDS}
    facet_combinations = []
    for number, html in volume_pages(www):
        volumes += 1
        matches = list(SESSION_PATTERN.finditer(html))
        if not matches:
            continue
        volumes_with_sessions += 1
        tag_sets.append("+".join(sorted({heading_element(html, match) for match in matches})))
        sessions_per_volume.append(len(matches))
        texts = [text_of(match.group(2)) for match in matches]
        heading_texts.extend(texts)
        volume_kinds = set()
        for text in texts:
            facet_combinations.append(facets_of(text))
            for word, pattern in KIND_PATTERNS.items():
                if pattern.search(text):
                    kind_headings[word] += 1
                    volume_kinds.add(word)
        for word in volume_kinds:
            kind_volumes[word] += 1
        # the sequence of marks: papers per heading and consecutive headings
        marks = [mark.upper() for mark in MARK_PATTERN.findall(html)]
        count = None
        volume_pairs = 0
        for mark in marks:
            if mark == "CEURSESSION":
                if count is not None:
                    papers_per_heading.append(count)
                    if count == 0:
                        volume_pairs += 1
                count = 0
            elif count is not None:
                count += 1
        if count is not None:
            papers_per_heading.append(count)
        if volume_pairs:
            pairs += volume_pairs
            pair_volumes += 1
            pair_volume_numbers.append(number)
    result = {
        "snapshot": snapshot(www),
        "volumes": volumes,
        "volumes_with_sessions": volumes_with_sessions,
        "headings": len(heading_texts),
        "distinct_texts": len(set(heading_texts)),
        "heading_elements": histogram(tag_sets),
        "sessions_per_volume": histogram(sessions_per_volume, key=lambda n: n if n < 11 else ("11-19" if n < 20 else "20+")),
        "papers_per_heading": histogram(papers_per_heading, key=lambda n: n if n < 30 else "30+"),
        "consecutive_headings_pairs": pairs,
        "consecutive_headings_volumes": pair_volumes,
        "consecutive_headings_since_4000": [n for n in pair_volume_numbers if n >= 4000],
        "facets": histogram(facet_combinations),
        "kind_words": {word: {"headings": kind_headings[word], "volumes": kind_volumes[word]} for word in KIND_WORDS},
    }
    return result


if __name__ == "__main__":
    www_dir = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    write_result(measure(www_dir), out_path)
