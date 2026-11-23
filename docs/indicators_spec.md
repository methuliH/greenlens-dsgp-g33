# GreenLens extraction spec: 19 indicators

You read a company's reading pack (table-like lines from the best pages of each year's reports) and write one CSV
row per company, year and indicator. Use only numbers that appear in the pack. Never guess, estimate or add up
business-unit figures to make a group total.

## Indicators
| Code | What it is | Target unit | Notes |
|---|---|---|---|
| GHG_S1 | Gross direct (Scope 1) GHG emissions, group total | tCO2e | kt x1,000, Mt x1,000,000 |
| GHG_S2 | Scope 2, location-based, group total | tCO2e | If only one Scope 2 figure and basis not stated, put it here and say so in measurement_basis |
| GHG_S2_MB | Scope 2, market-based, group total | tCO2e | Only if the report labels it market-based |
| GHG_S3 | Total Scope 3 | tCO2e | Total only, not a single category |
| EN_TOT | Total energy consumption | GJ | MWh x3.6, GWh x3,600, TWh x3,600,000, TJ x1,000, PJ x1,000,000, toe x41.868 |
| EN_ELEC | Electricity consumption (electricity only) | kWh | MWh x1,000, GWh x1,000,000. If the figure mixes heat or steam, status unclear with note |
| EN_REN_PCT | Share of renewable energy in total energy consumption | % (0-100) | Not share of renewable electricity generation |
| WA_WD | Total water withdrawal | m3 | thousand m3 x1,000, million m3 / hm3 / Mm3 x1,000,000, megalitres x1,000 |
| WA_CONS | Water consumption (withdrawal minus discharge, or as the report defines it) | m3 | Note the definition used |
| E-WST-GEN | Total waste generated | MT (tonnes) | Hazardous + non-hazardous may be summed when both are group totals; say so in measurement_basis |
| E-WST-HAZ | Hazardous waste generated | MT (tonnes) | |
| S-EMP | Employees at year end, headcount | persons | Note if FTE or average |
| S-WOMEN-PCT | Women as % of total workforce | % | |
| S-LTIFR | Lost-time injury frequency rate, employees (or employees + contractors) | rate | Note basis: per 1,000,000 hours or per 200,000 hours, and who is covered |
| S-FATAL | Work-related fatalities (employees + contractors if given together) | persons | Note coverage |
| G-BOARD-SIZE | Members of the board of directors (or supervisory board) at year end | persons | Note which board |
| G-BOARD-IND-PCT | Independent board members as % of board | % | If only counts, compute count/size x100 and say so |
| G-BOARD-WOMEN-PCT | Women as % of board | % | Same rule |
| FIN_REV | Group revenue / net sales | million, in the reported currency | unit = "EUR m", "CHF m", "SEK m", "USD m" etc. Do not convert currencies |

## Rules
- data_year is the reporting (fiscal) year of the figure. Take each year's value from that year's own documents in the
  pack (the block headed "year Y"). Ignore prior-year comparison columns unless the year's own documents are missing.
- Fiscal years like 2022/23 belong to the year in the block header.
- Status: `reported` (value found), `not_reported` (the report says it is not reported or not applicable),
  `unclear` (not found in the pack, ambiguous, partial scope, or conflicting). When in doubt, `unclear`.
- needs_review = 1 for anything rounded, from a chart or infographic, partial, computed, or assumption-based; else 0.
- Stellantis before 2021: Stellantis N.V. is the renamed FCA N.V.; use FCA figures and note that PSA is excluded.
- Numbers: European formats use "." for thousands and "," for decimals; check against the context.

## CSV columns (exact order, UTF-8 with BOM)
company, data_year, indicator_code, disclosure_status, value_numeric, unit, source_value_text, source_unit,
measurement_basis, boundary, pdf_page, source_file, source_url, source_excerpt, verification_status, needs_review,
extraction_method, note

- source_file: the document name shown in the pack line, plus ".pdf". pdf_page: the page number shown (pN).
- source_excerpt: the exact label and number from the pack (under 200 characters).
- boundary: "Group" unless stated otherwise. source_url: leave empty.
- verification_status: "LLM (Claude agent), not human-checked". extraction_method: "llm_agent".
- Every year in the pack gets all 19 rows, including unclear ones (value empty, unit filled).
