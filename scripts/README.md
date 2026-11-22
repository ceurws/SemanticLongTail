# Measurement scripts

Standard library Python only, run with `python3 -I` on a host that holds a
mirror of the volume pages as `<www>/Vol-N/index.html`. No page is copied
into this repository; the result JSON goes to `data/<run date>/`.

| script | measures | first published in |
| --- | --- | --- |
| `sessions.py` | CEURSESSION headings: elements, sessions per volume, papers per heading, consecutive headings, facets, kind words | [semantify discussion 74](https://github.com/ceurws/semantify/discussions/74), 2026-11-06 |
| `affiliations.py` | the marker after an editor name and the affiliation block below the editors, both conventions | [semantify #67](https://github.com/ceurws/semantify/issues/67#issuecomment-6705865844), 2026-11-07 |
| `ceurpages.py` | shared page access, snapshot description, histogram | |
| `round0.py` | Round 0: `ceursemantify --generate` per volume into a year tree, per volume status generated, failed or skipped with message, year and its source, counts per year, run time | SemanticLongTail #1, 2026-11-18 |
| `timestamps.py` | year of the modification time of index.html, index.html.orig and the oldest file of a volume directory against CEURPUBDATE, and the years they give for the volumes Round 0 skipped | semantify #78, 2026-11-18 |
| `yearvotes.py` | votes of ten sources on the year of each volume, the requirement being the publication year: sources with a vote and largest agreeing group per volume, agreement of each source with the majority and with CEURPUBDATE, volumes without majority | SemanticLongTail #1, 2026-11-20 |
| `templateversions.py` | template version per volume, C1 the declared CEURVERSION, C2 otherwise the structural signature dated by its first use: markup layer plain, CEUR classes or RDFa, declared versions with volume ranges, dates and changed template elements, signatures of the undeclared volumes, first use of every template element; with --pre-out the boilerplate of the volumes before the CEUR classes and of the plain volumes after them | SemanticLongTail #6, 2026-11-22 |

```bash
python3 -I sessions.py /path/to/www data/2026-11-10/sessions.json
python3 -I affiliations.py /path/to/www data/2026-11-10/affiliations.json
python3 -I round0.py --all --www /path/to/www --tree /path/to/tree --log data/2026-11-18/round0.jsonl --ceursemantify /path/to/ceursemantify
python3 -I timestamps.py /path/to/www data/2026-11-18/round0.jsonl data/2026-11-18/timestamps.json
python3 -I yearvotes.py --www /path/to/www --log data/2026-11-18/complete.jsonl --browser /path/to/volumes.json --out data/2026-11-20/yearvotes.json
python3 -I templateversions.py --www /path/to/www --years data/2026-11-20/yearvotes.json --last 4332 --snapshot 1a8d36cc89 --out data/2026-11-18/templateversions.json
python3 -I templateversions.py --www /path/to/www --years data/2026-11-20/yearvotes.json --last 4332 --boundary 559 --snapshot 1a8d36cc89 --pre-out data/2026-11-18/preceur.json
```

The scripts of 2026-11-06 and 2026-11-07 were not committed; these are
written again from the counting rules recorded with the published numbers.
Where a result differs from a published number, the difference is reported
in the issue of the run, see SemanticLongTail #1.
