"""Where the pipeline reads and writes files.

Reports (PDF/XLSX) are NOT stored in git. Point the pipeline at your local copy:

    Windows (Command Prompt):  set GREENLENS_REPORTS=C:\\path\\to\\reports
    Windows (PowerShell):      $env:GREENLENS_REPORTS = "C:\\path\\to\\reports"
    macOS / Linux:             export GREENLENS_REPORTS=/path/to/reports

The reports folder must contain one sub-folder per company, e.g. reports/Holcim/*.pdf.
If the variable is not set, data/reports/ inside this repo is used.

GREENLENS_WORK (optional) changes where caches, reading packs and results go
(default: data/ inside this repo).
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS = os.environ.get("GREENLENS_REPORTS", os.path.join(REPO, "data", "reports"))
WORK = os.environ.get("GREENLENS_WORK", os.path.join(REPO, "data"))
SOURCES = os.path.join(REPO, "data", "sources")
