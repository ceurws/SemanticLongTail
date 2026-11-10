# Data policy

- No CEUR-WS PDFs and no volume pages are stored here: CEUR-WS forbids
  third-party mirroring of its site or parts of it. Volumes and papers are
  referenced by their URL `https://ceur-ws.org/Vol-N/`.
- Every measurement is stored with the date of the snapshot of the volume
  pages it was run on and the script in `scripts/` that produced it.
- A residue cluster is stored as its count, first and last volume, variants
  and example volume numbers, not as the page text.
- A graph walk is stored as its sequence of PentaLinks, pid, slug, type,
  kgUrl, webUrl, with the volume numbers it was written from and the forks
  found: slug with several pids, slug with no pid, pid depending on time.
- A competency question is stored as a named query with the date of its run
  and its result against the endpoint on ceur-ws.org.
- A deduced value is stored as a proposal with its evidence and confidence,
  and its review state per the provenance notation.
- Third-party data enters only with a license or a written permission.
