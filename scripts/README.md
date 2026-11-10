# Measurement scripts

Standard library Python only, run with `python3 -I` on a host that holds a
mirror of the volume pages as `<www>/Vol-N/index.html`. No page is copied
into this repository; the result JSON goes to `data/<run date>/`.

| script | measures | first published in |
| --- | --- | --- |
| `sessions.py` | CEURSESSION headings: elements, sessions per volume, papers per heading, consecutive headings, facets, kind words | [semantify discussion 74](https://github.com/ceurws/semantify/discussions/74), 2026-11-06 |
| `affiliations.py` | the marker after an editor name and the affiliation block below the editors, both conventions | [semantify #67](https://github.com/ceurws/semantify/issues/67#issuecomment-6705865844), 2026-11-07 |
| `ceurpages.py` | shared page access, snapshot description, histogram | |

```bash
python3 -I sessions.py /path/to/www data/2026-11-10/sessions.json
python3 -I affiliations.py /path/to/www data/2026-11-10/affiliations.json
```

The scripts of 2026-11-06 and 2026-11-07 were not committed; these are
written again from the counting rules recorded with the published numbers.
Where a result differs from a published number, the difference is reported
in the issue of the run, see SemanticLongTail #1.
