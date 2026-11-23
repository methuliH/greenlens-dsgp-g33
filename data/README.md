# Data

| Folder | In git? | Contents |
|---|---|---|
| `sources/` | Yes | `download_list_all.csv/.json`: every report link (company, year, type, URL, size, check status) |
| `results/` | Yes | Extracted indicator CSVs |
| `results/llm19/` | Yes | One CSV per company, 19 indicators × years (pass 1) |
| `results/pilot/` | Yes | EVN and A2A method comparison (LLM vs rule-based) |
| `reports/` | **No** | Local PDFs/XLSX, one folder per company (or use `GREENLENS_REPORTS`) |
| `cache/`, `candidates/`, `packs19*/`, `reading_packs*/` | **No** | Intermediate files, rebuilt by the scripts |

## CSV layout (team format)

`company, data_year, indicator_code, disclosure_status, value_numeric, unit, source_value_text, source_unit,
measurement_basis, boundary, pdf_page, source_file, source_url, source_excerpt, verification_status,
needs_review, extraction_method, note`

- `disclosure_status`: `reported`, `not_reported` or `unclear`
- `needs_review = 1`: a person should check the value (unusual jump, boundary doubt, value taken from a chart)
- Units and indicator codes: see `docs/indicators_spec.md`

## Getting the reports

Run `python src/extraction/download_all.py` to download every link in `sources/download_list_all.json` into the
reports folder. Links that fail are written to `sources/failed_links.csv`; download those in a browser.
