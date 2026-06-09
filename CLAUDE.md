# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** (not a traditional software project) that generates structured technical evaluation reports from meeting transcripts and supporting documents. The core question it answers: "Is this technology viable and worth further exploration?"

The project is for a Chinese energy/environmental company's technical department. The primary skill definition lives in `.claude/commands/tech-exchange-evaluation.md`.

## How to Run

```
/tech-exchange-evaluation          # Default: 4-chapter condensed version
/tech-exchange-evaluation --full   # Full 8-chapter version
```

Place input materials first:
- `input/transcript.md` — meeting transcript (required)
- `input/counterpart/` — counterpart's technical documents (optional, PDF/md)
- `input/benchmark/` — internal reference documents (optional)

Output goes to `output/技术评估报告_{YYYYMMDD}_{技术主题}.docx`.

## Architecture: Three-Phase Parallel Pipeline

```
Phase 1 (parallel)
├─ Agent-A [素材读取] → output/.tmp_materials.md
└─ Agent-B [行业检索] → output/.tmp_benchmarks.md (6x Tavily searches)

Phase 2 (serial, after both Phase 1 agents complete)
└─ Agent-C [报告撰写] → CRITIC adversarial review + FACT-CHECKER numerical verification
                         → output/report_draft.md

Phase 3 (serial)
└─ Main Agent [DOCX] → minimax-docx skill → output/*.docx
```

**Phase 1** launches two `general-purpose` agents in a single message (parallel tool calls). Agent-A reads all input files and extracts structured data. Agent-B reads the transcript, identifies the technology theme, then fires 6 parallel Tavily searches (standards, international standards, economic data, technical parameters, compliance risks, counterpart verification).

**Phase 2** launches Agent-C after both Phase 1 agents finish. Agent-C synthesizes both temp files into the report, runs CRITIC adversarial review and FACT-CHECKER numerical verification, writes `report_draft.md`, and cleans up temp files.

**Phase 3** calls the `minimax-docx` skill (external, not in this repo) to convert the Markdown draft to a formatted Word document.

## Four Iron Rules (governing principles)

1. **Fact vs. judgment** — counterpart claims must be sourced (verbal / document name), conclusions labeled as "analysis"
2. **Unknown is unknown** — no hallucination; gaps go to the "to-verify" list
3. **Conflicts must surface** — contradictions between counterpart claims and benchmarks are explicitly flagged
4. **Professional restraint** — no names in body text, use "我方"/"对方" instead

## Key Dependencies & MCP Servers

- **tavily-search MCP** (`.mcp.json` / `.claude/mcp-servers/tavily-search.py`): Custom MCP server wrapping the Tavily Search API via JSON-RPC stdio. Used by Agent-B for industry research.
- **minimax-docx** (external skill): Converts Markdown to Word. Required for Phase 3.
- **AnySearch** (`.claude/skills/anysearch/`): Third-party search skill providing web search, vertical domain search, batch search, and URL extraction.

## Conventions

- All report chapter numbering uses Chinese numerals (一、二、三...) for main chapters, Arabic decimals (4.1, 4.2...) for sub-sections
- The `.gitignore` excludes `input/`, `output/`, `.claude/mcp-servers/`, and `.claude/skills/` — these are local-only
- `.docx` files in `input/` must be converted to Markdown first: `pandoc xxx.docx -o xxx.md`
- PDFs over 20 pages are read in segments; images need OCR via `mcp__utools__utools_ocr_ocr_extract_content`
- Unit consistency is critical: always convert to the same unit before comparing numerical values (see memory note on unit consistency)
