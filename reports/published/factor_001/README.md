# Momentum #001 publication

This directory contains the self-contained [HTML](momentum_001.html) and matching [PDF](momentum_001.pdf) presentation of the closed Momentum #001 research. The publication date is 2026-11-16 (Asia/Shanghai). Its single authoritative source is `build_report.py`, which formats saved documents, tables and figures. It does not load market prices, construct factors, run research or change any frozen record.

From the repository root on Windows:

```powershell
.venv\Scripts\python.exe -B reports/published/factor_001/build_report.py
```

The build requires the project's pinned Python environment, `websocket-client==1.9.2`, and a locally installed Chromium browser. The default is `C:\Program Files\Google\Chrome\Application\chrome.exe`; set `PUBLICATION_CHROME` to another Chromium executable if needed. For PDF inspection, it uses `PyMuPDF==1.26.7` installed separately under this directory's ignored `.venv/qa` folder. To prepare that isolated inspection dependency:

```powershell
.venv\Scripts\python.exe -B -m pip install --target reports/published/factor_001/.venv/qa PyMuPDF==1.26.7
```

The script verifies original seals and saved-output hashes before and after formatting. It reads source documents plus saved structured tables; images are embedded into the HTML as data URLs, and the same HTML is printed to A4 PDF by headless Chromium. The page blocks HTTP(S) requests during printing. CSS, equations and images are self-contained. The publication manifest lists every input hash, the browser version, output hashes and automated checks. Temporary browser profiles, PDF contact sheets and the inspection dependency are under `.venv/` and remain Git-ignored.

The PDF check confirms A4 pages, page numbers, required text, image inclusion, font entries and text bounds. Embedded figures retain the original saved data and labels. Inspect pages visually for final editorial approval; the automated check cannot prove every caption or font is aesthetically ideal. The HTML and PDF share the same content; browser pagination alone differs.

The current conclusion is **Watchlist — Mixed Temporal Evidence**. Validation passed; the frozen final held-out test was Not Supported. The report is a presentation archive, not a replacement for source research, protocols or the private Git-ignored market-data backup. Rebuilding this publication does not authorize a new factor evaluation or a repeat of the final test.
