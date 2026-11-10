# Content policy for AI agents

This repository holds a **technical report** on the semantic concepts that
CEUR-WS volume pages and papers carry beyond their CEUR tags. It is not
published via CEUR-WS, but it follows the
[CEUR-WS Policy on AI-Assisting Tools](https://ceur-ws.org/GenAI/Policy.html)
(Salatino, Fornari, Zdravkovic, CC BY 4.0), whose use outside CEUR-WS is
permitted subject to attribution.

## Hard rules

0. **NEVER build the report locally.** No `scripts/tex2pdf`, no `pdflatex`,
   no `latexmk` — the PDF is built by CI on push.
1. AI assistance is limited to **spelling/grammar**, **translation of text
   dictated by the authors**, **formatting/build tooling** and the agentic
   work that is explicitly part of the method: running the measurement
   scripts, computing the residue, collecting graph walk data from real
   volumes, running competency questions against the endpoint.
2. Everything outside that scope — **the research question, which concepts
   are accepted into the model, conclusions, arguments, prose, the abstract,
   the title** — is authored by the human authors. Text an agent rewords is
   generated text and does not go into `main.tex`.
3. Sections in `main.tex` stay **EMPTY** until the authors write them.
4. **No AI-generated visual aids.** Charts are produced deterministically by
   scripts from the data; diagrams are drawn by the authors. An agent does
   not write diagram source (PlantUML, SVG, TikZ). A graph walk is data in
   `data/`, not a drawing.
5. Only **verified** bibliographic metadata belongs in `references.bib`.
   Never fabricate references, DOIs, page numbers or claims.
6. **No CEUR-WS PDFs in this repository.** CEUR-WS forbids third-party
   mirroring. The data holds volume and paper URLs, counts, residue
   clusters, walks and query results only.
7. **No third-party data without a license or a written permission.**
8. **No internal sources**: no board mails, no internal host names, no numbers
   from manuscripts without a DOI. A number in the report comes from a
   script in `scripts/` run on a dated snapshot, or from a cited source.
9. AI agents are **never authors** (CEUR-WS HOWTOSUBMIT FAQ 15).
10. Every agent contribution is recorded in [PROVENANCE.md](PROVENANCE.md)
    and in the issues with the provenance notation of the README; the
    **Declaration on Generative AI** is finalized by the authors from that
    record.
11. The report must be **self-contained**: every term is defined in the text,
    links only point to further material.
12. A deduced value, an organisation for a printed affiliation, a person for
    a name, a conference for a long name, is a **proposal with evidence and a
    confidence**. It is never recorded as a fact and never written back into
    a volume page.

## Allowed agent tasks

- Maintain the CEURART scaffold, build system and `.gitignore`.
- Fix LaTeX/build errors and formatting.
- Format author-provided bibliography entries.
- Resolve and fill **verified** author ORCIDs/affiliations (from Wikidata/ORCID).
- Write and run the measurement and residue scripts in `scripts/` and record
  their results in `data/` with the snapshot date, as described in the issues.
- Collect graph walk data for a concept from real volumes.
- Run competency questions as named queries against the endpoint and record
  the results.
