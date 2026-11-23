# ESG extraction pipeline

This page explains how GreenLens turns company reports (PDF/XLSX) into a table of ESG indicators, and how
well each method worked. The indicators, units and rules are defined in [indicators_spec.md](indicators_spec.md).

## Overview

```
reports (PDF/XLSX)
   │  extract_pages.py      text of every page, cached as JSON lines
   ▼
page cache
   │  build_packs.py        score pages for "table-ness", keep the best page per indicator group per year
   ▼
reading pack (~6 KB per report instead of ~700 KB)
   │  LLM                   reads the pack and fills the 19-indicator CSV with value, page and quote
   ▼
results CSV ──► validate19.py (units, ranges, year-on-year jumps) ──► combined CSV
   │
   └─ followup19.py         extra pages only for indicator groups the LLM marked "unclear"
```

## Scripts (`src/extraction/`)

| Script | Purpose |
|---|---|
| `paths.py` | Where reports, caches and results live (`GREENLENS_REPORTS`, `GREENLENS_WORK`) |
| `fetch_sources.py` | `probe` checks each link in a link list (status, size, type); `download` fetches approved ones |
| `download_all.py` | Stand-alone downloader (standard library only) with web.archive.org fallback and PDF/XLSX check |
| `extract_pages.py` | Caches page text with PyMuPDF; XLSX sheets become "pages" |
| `candidates.py` | Keyword search for likely pages (used by the rule-based baseline) |
| `rule_extract.py` | Rule-based baseline: regex label + number + unit |
| `page_dump.py` | First version of the LLM reading packs (kept for comparison) |
| `page_select.py` | Page scoring: indicator labels, units, large numbers and year columns; penalises GRI index pages and prose |
| `build_packs.py` | Builds one reading pack per company covering all years and all 19 indicators |
| `followup19.py` | Second-pass packs (ranks 2–4) for indicator groups still mostly unclear |
| `validate19.py` | Checks schema, units, % ranges and 19 rows per year; flags jumps over 5× year on year; combines files |
| `coverage.py` | Checks whether the reference values are visible in a pack at all |
| `score.py` | Precision and recall against a team member's manual CSV |

## Method comparison (pilot)

The reference for each pilot company was a team member's manually extracted CSV.

**EVN** (14 reports, 98 values; blind test):

| Method | Values given | Match reference | Precision | Recall |
|---|---|---|---|---|
| Rule-based | 73 | 4 | 5% | 19% |
| LLM | 61 | 54 | 89% (98% on the number itself) | 81% |

**A2A** (16 reports, using the improved packs plus follow-up):

| Method | Values given | Match reference | Precision | Recall |
|---|---|---|---|---|
| Rule-based | 85 | 13 | 15% | 57% |
| LLM | 55 | 51 | 93% | 75% |

Most disagreements were about definitions, not reading errors:
- **Scope 2 boundary (A2A 2024–25):** one answer included electricity distribution losses (134,094 + 113,926 = 248,020 tCO2e) and the other did not. **The team needs to agree a rule.**
- **EVN 2023 total energy:** own consumption vs including generation fuel.

Caveat: some A2A reference values had been seen before the test, so A2A is not fully blind. EVN was.

**Conclusion:** use the LLM method, keep the rule-based method as a baseline, and have a person spot-check rows marked `needs_review`.

## Token reduction

| Pack | Text per report | Reference values visible (EVN / A2A) |
|---|---|---|
| Full report | ~700 KB | 100% |
| Keyword pages (`page_dump.py`) | 6.8–8.2 KB | 78% / 70% |
| Table-scored pages (`page_select.py`) | 5.4–5.9 KB | 90% / 75% |
| + follow-up pages | + ~4 KB per missing group | recovers most of the rest |

## 19-indicator run, pass 1 (20 companies)

Output: `data/results/ALL_20_companies_19_indicators_pass1.csv`: 3,553 rows, of which 1,083 are reported values
and 548 are flagged `needs_review`.

Share of company-years with a reported value:

| Indicator | Coverage | Indicator | Coverage |
|---|---|---|---|
| LTIFR | 52% | Hazardous waste | 30% |
| Scope 1 | 46% | Total energy | 26% |
| Fatalities | 46% | Waste generated | 24% |
| Employees | 43% | Water consumption | 21% |
| Revenue | 39% | Scope 3 | 20% |
| Scope 2 (location) | 39% | Board women % | 20% |
| Board size | 39% | Scope 2 (market) | 18% |
| Water withdrawal | 35% | Board independence % | 17% |
| Women % | 35% | Electricity | 16% |
| | | Renewable share | 11% |

Why coverage is low:
- Some reports were missing or the wrong type. 205 extra reports are now being downloaded.
- Some reports give totals only for business units.
- Older reports often don't disclose the indicator at all.
- Only the top page per group was read.
- Pass 1 rule: each year's value must come from that year's own report.

**Pass 2 (planned):** use the new downloads and the follow-up packs. Also allow the prior-year column of the following year's report, marked `needs_review = 1`.
