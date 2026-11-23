# GreenLens – DSGP Group 33

ESG analytics platform for sustainability report data (DSGP Group 33).

GreenLens combines **physical climate risk**, **emissions data** and **AI (LLM) extraction of ESG indicators**
from the annual and sustainability reports of EU-listed companies, and forecasts how those indicators develop.

> BSc (Hons) Artificial Intelligence and Data Science – Data Science Group Project (IIT / RGU)
> Supervisor: Mr. Dilanka Perera

---

## Contents

- [Project status](#project-status)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [ESG extraction pipeline](#esg-extraction-pipeline)
- [Data](#data)
- [Team](#team)
- [Contributing](#contributing)

## Project status

| Component | Status |
|---|---|
| Report collection (31+ companies, 2010–2025) | In progress: about 19.5 GB collected, gap-filling downloads running |
| ESG indicator extraction | |
| Physical climate risk | Planned |
| Forecasting | Planned |
| Web application / dashboard | Planned |

## Repository structure

```
greenlens-dsgp-g33/
├── README.md               ← you are here
├── requirements.txt        ← Python packages
├── docs/
│   ├── indicators_spec.md       ← the 19 ESG indicators, units and extraction rules
│   └── extraction_pipeline.md   ← how the extraction works, plus evaluation results
├── src/
│   └── extraction/         ← download, PDF text, page selection, rule-based baseline, scoring
├── data/
│   ├── README.md           ← what is (and is not) stored in git
│   ├── sources/            ← list of report download links (no PDFs)
│   ├── results/            ← extracted ESG indicator CSVs
│   └── reports/            ← local reports folder (ignored by git)
└── notebooks/              ← exploration and analysis notebooks
```

## Getting started

Requirements: Python 3.10+.

```bash
git clone https://github.com/methuliH/greenlens-dsgp-g33.git
cd greenlens-dsgp-g33
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

The reports themselves are too large for GitHub (and are the companies' copyright), so each member keeps them
locally. Tell the scripts where they are:

```bash
set GREENLENS_REPORTS=C:\path\to\reports          # Windows Command Prompt
$env:GREENLENS_REPORTS = "C:\path\to\reports"     # Windows PowerShell
export GREENLENS_REPORTS=/path/to/reports         # macOS / Linux
```

The folder needs one sub-folder per company (`reports/Holcim/*.pdf`, `reports/Mondi/*.pdf`, ...).
If you skip this step, `data/reports/` is used.

## ESG extraction pipeline

All scripts are in `src/extraction/` and are run from that folder (`cd src/extraction`).

| Step | Command | Output |
|---|---|---|
| 1. Download missing reports | `python download_all.py [Company ...]` | PDFs/XLSX in the reports folder, `failed_links.csv` |
| 2. Cache page text | `python extract_pages.py <Company> ...` | `data/cache/<Company>/*.jsonl` |
| 3. Build reading packs | `python -c "import build_packs as b; b.build('<Company>')"` | `data/packs19/<Company>.txt` |
| 4. LLM extraction | An LLM reads each pack and fills the 19-indicator CSV (see spec) | `data/results/llm19/<Company>_llm19.csv` |
| 5. Follow-up packs for gaps | `python -c "import followup19 as f; f.build('<Company>', '<csv>')"` | `data/packs19_fu/<Company>.txt` |
| 6. Validate and combine | `python validate19.py ../../data/results/llm19 ../../data/results/combined.csv` | combined CSV and a coverage report |
| Baseline | `python candidates.py <Company>` then `python rule_extract.py <Company>` | `data/results/<Company>_rule_based.csv` |
| Evaluation | `python score.py <Company> <method>` | precision / recall vs the team's manual CSV |

**Key result so far:** on the two pilot companies, LLM extraction from selected pages reached
89–93% precision and 75–81% recall against the team's manual reference. The rule-based baseline reached 5–15% precision.
Reading only table-like pages cut the text sent to the LLM from about 700 KB to about 6 KB per report.
Details are in [docs/extraction_pipeline.md](docs/extraction_pipeline.md).

## Data

See [data/README.md](data/README.md). In short: link lists and extracted CSVs are tracked; PDFs, caches
and reading packs are not.

Main output: `data/results/ALL_20_companies_19_indicators_pass1.csv`. It has 3,553 rows covering 20 companies,
19 indicators and the years 2010–2025. Every row has `verification_status = "LLM (Claude agent), not human-checked"`.
Rows marked `needs_review = 1` should be checked by a person before use.

## Team

| Member | - |
|---|---|
| Nelum Kumarasinghe | -|
| Methuli Heenkenda | _add area_ |
| Enara Wickramasinghe | _add area_ |
| Wageesha Vihangana | _add area_ |


