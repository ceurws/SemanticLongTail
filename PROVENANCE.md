# Provenance log

One row per agent contribution to this repository. The authors finalize the
Declaration on Generative AI in `main.tex` from this log. Categories follow the
[GenAI Usage Taxonomy](https://ceur-ws.org/GenAI/Taxonomy.html); work that is
part of the method is marked as method.

| date | tool and model | agent | contribution | taxonomy category or method | commit or issue | review |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-10 | Claude Code, claude-fable-5-1 | Agent/Guido | repository scaffold cloned from ceurws/GenAIDeclarationPaper: CEURART files, build workflow, empty main.tex, AGENTS.md, README with the research question and method dictated by Wolfgang Fahl, this log, data policy | Formatting assistance | initial commit | 👁️🧑 Wolfgang Fahl ❓ |
| 2026-11-18 | Claude Code, claude-opus-5-5 | Agent/Guido | scripts/round0.py written and run: Round 0 generation of all volumes of the snapshot of 2026-11-18 10:00 with pyCEURsemantify 0.0.8 into a year tree outside the repository; per volume log and summary in data/2026-11-18, the trial on 420 volumes beside it | method | #1 | 👁️🧑 Wolfgang Fahl ❓ |
| 2026-11-18 | Claude Code, claude-opus-5-5 | Agent/Guido | scripts/timestamps.py written and run: modification time years of index.html, index.html.orig and the oldest file per volume against CEURPUBDATE on the snapshot of 2026-11-18 10:00, and the years they give for the volumes Round 0 skipped; result in data/2026-11-18/timestamps.json | method | #1, ceurws/semantify#78 | 👁️🧑 Wolfgang Fahl ❓ |
| 2026-11-20 | Claude Code, claude-opus-5-5 and claude-fable-5-2 | Agent/Evi | scripts/yearvotes.py written and run: votes of ten sources on the year of each volume on the snapshot of 2026-11-18 10:00, histograms of their agreement; result in data/2026-11-20/yearvotes.json | method | #1, ceurws/semantify#78 | 👁️🧑 Wolfgang Fahl ❓ |
| 2026-11-20 | Claude Code, claude-fable-5-2 | Agent/Evi | references.bib: entries FahlHOD23 and FahlHLBD27 added, metadata taken from the DOI record, the Springer author proof and the bibliography of the published ISWC 2026 chapter | Citation management | this commit | 👁️🧑 Wolfgang Fahl ❓ |
| 2026-11-20 | Claude Code, claude-fable-5-2 | Agent/Evi | Method section: first paragraph taken down from the dictation of Wolfgang Fahl; speech recognition errors corrected (CEUR-WS, semantification, semantify), the two repository URLs inserted where the dictation says at the URL, are added in the last sentence | Grammar and spelling check | this commit | 👁️🧑 Wolfgang Fahl ❓ |
| 2026-11-20 | Claude Code, claude-fable-5-2 | Agent/Evi | Method: first sentence and round 0 paragraph translated from the German dictation of Wolfgang Fahl, work questions corrected to research questions as dictated; Research Question: the two paragraphs of the README taken over verbatim, table of research questions and their issues built from the issue titles, the sentence leading to the table worded by the agent and shown to Wolfgang Fahl before the commit | Text Translation, Formatting assistance | this commit | 👁️🧑 Wolfgang Fahl ✓ shown before commit |
