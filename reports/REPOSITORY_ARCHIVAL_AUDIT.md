# Repository archival audit

Date: 2026-11-14 (Asia/Shanghai). Documentation-only preparation; no staging, commit, push, tag, deletion, rename, move, history rewrite, ignore change or market evaluation.

## Navigation and organization

The root README now identifies the [canonical final assessment](01_momentum_alpha_assessment_final.md), [Factor Library](FACTOR_LIBRARY.md), structured record, evidence chronology and backup needs. The library already links directly to the final assessment and is hash-pinned; it was left unchanged.

Similar report names represent distinct historical stages, not disposable duplicates: original research, exploration close-out, validation, pre-test assessment, final protocol/results and final assessment. #001-B cumulative/incremental and #001-C controls remain independent studies. Documentation links resolve ambiguous names without moving sealed artifacts. Historical helper names/status messages are preserved for compatibility.

## Git findings

At entry, four tracked files had prior changes: `config/README.md`, `requirements.txt`, `research/01_momentum.ipynb`, `src/evaluation/__init__.py`. Their diffs add universe documentation, three pinned dependencies, evaluation exports and saved research evidence. The notebook changed from 4 to 15 cells and 4 to 11 saved outputs. These changes predate this cleanup and remain preserved. README is additionally modified by this task; this audit is new.

The index was empty. The initial nonignored tracked/untracked inventory contained 79 files; none exceeded 1 MiB. There were no tracked ignored files. A heuristic scan of candidate text, including notebooks, found no private-key, common token-shape, credential-assignment or credential-bearing URL matches. This is not a guarantee that all possible secrets are absent. `.env` contents were not read or printed.

Existing ignore rules cover `.env`, `.env.*` (including `.env.example`), `.venv`, root datasets, notebook-relative data, Python caches and build outputs. Eight local `.pyc` files outside `.venv`/`.git` were observed and retained. The largest local file is the ignored frozen price matrix, 20,437,080 bytes; other large files are ignored vendor responses and research audits. No data was removed.

Completed-study configurations, reports, notebooks, figures, scripts and tests are appropriate commit candidates after review. `config/universe.csv` is intentional frozen security metadata, not a price panel. Raw/processed market data must remain ignored. Vendor/source redistribution rights are not established by this audit; review terms and saved notebook outputs before public publication. No network/licensing research was performed and no legal clearance is implied.

## Recommended commands — not executed

Run from the repository root after review. Scoped staging includes the completed research code/documentation but excludes root `.env`, `.venv` and `data`; ignored legacy research data also remains excluded. Do not use `-f` or blanket `git add -A`.

```powershell
git status --short
git diff --stat
git diff --cached --stat
git -c core.autocrlf=false add -- README.md requirements.txt config factors reports research scripts src tests
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

Local `core.autocrlf=true` risks changing sealed bytes through staging/checkout conversion. The per-command override preserves file bytes without altering local settings. Before committing, compare staged blobs with working files:

```powershell
@'
import hashlib, subprocess
from pathlib import Path
names = subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACM','-z']).decode().split('\0')
for name in filter(None, names):
    blob = subprocess.check_output(['git','show', ':' + name])
    assert hashlib.sha256(blob).digest() == hashlib.sha256(Path(name).read_bytes()).digest(), name
print('Staged bytes match working files')
'@ | .venv\Scripts\python.exe -B -
```

Stop on a mismatch; do not reseal research. After staged review and backup verification, suggested commit/tag commands are:

```powershell
git -c core.autocrlf=false commit -m "Archive Momentum 001: Watchlist after final test Not Supported"
git tag --list momentum-001-closed-v1.0.0
git tag -a momentum-001-closed-v1.0.0 -m "Momentum 001 closed: Watchlist - Mixed Temporal Evidence; validation Pass; final held-out Not Supported"
```

Create the tag only if its name is absent; never replace an existing tag. No push is proposed automatically. The tag identifies code/documentation, not a complete dataset archive. Restore using a byte-preserving checkout, e.g. `git clone --config core.autocrlf=false <repository-url> <archive-directory>`, before restoring the matching private backup and pinned environment. Do not normalize sealed files in an editor.

## Separate local backup required

Keep the entire root `data/` tree with original relative paths and bytes:

- `data/market/2026-11-12/`: frozen panel, coverage, batch records and diagnostics.
- `data/universe/`: original constituent source snapshot/provenance.
- `data/raw/` and `data/processed/`: vendor responses, validated caches and metadata, including SPY.
- `data/protocols/`: frozen source snapshots, preparation receipts and tests required by seals.
- `data/validation/`: execution marker, archived original report prefix, driver, audits, tests and results.
- `data/final_test/`: exclusive marker, tested driver, preflight evidence, final results and manifests.
- `data/research/`: exploration, #001-B, incremental and #001-C outputs, figures, masks, manifests and test evidence.
- Any legacy `research/data/` or other ignored notebook-local datasets: preserve without promoting them to validated caches.

Use access-controlled, checksum-verified storage outside this working tree and test restoration with read-only checks. Some report figures and audit links require these ignored artifacts; Git alone is insufficient. Back up `.env` only through a separate encrypted secrets mechanism if needed. `.venv` may be retained for local environment provenance, but pinned dependencies/protocol versions remain authoritative and fresh installation has not been verified. Generated caches need not be backed up; none were deleted.

## Integrity and status agreement

Read-only verification covers final seal/environment/validation lineage, #001-B, incremental and #001-C manifests, final execution artifacts, prior-file hashes, library references and closure hashes. Check pinned paths individually: new documentation legitimately extends directories without changing historical files.

The final assessment, index and structured record agree: Factor 001, Momentum `P[t]/P[t-5] - 1`, negative orientation, validation Pass, final test Not Supported, Watchlist, Closed. Closed is completion, not success. README is not pinned by the historical seals; archived research files were not edited.

`python -B scripts/verify_momentum_001_final_test.py` is an offline byte/version verifier. Its hardcoded preparation-status text is stale: the preserved marker/result record one completed final execution. The original standalone validation verifier flags the authorized report append; final lineage checks account for the original archived prefix/full-report hash without changing its seal. Do not invoke execution drivers, study runners or download scripts as archival verification. No pytest or market evaluation was rerun for this documentation audit.


## Authorized staging follow-up

The corrected staging scope explicitly includes `factors/` and all `src/` modules, including `src/data/` (source code, not a market-data directory). The complete per-file ignored research backup inventory is recorded in [ignored_research_backup_inventory.json](archive/momentum_001/ignored_research_backup_inventory.json). It records paths, sizes and SHA-256 values only, not dataset contents or secrets. Staging is authorized in this follow-up; commit, push and tag remain unexecuted.

Staging byte check: six unchanged tracked files retained older normalized index blobs despite scoped add. Their exact existing working bytes were staged with Git hash-object --no-filters and update-index --cacheinfo; no working files were normalized or edited. All source modules are now represented byte-for-byte. Default diff --check reports preserved CRLF endings; with core.whitespace=cr-at-eol, eight pre-existing trailing-whitespace findings remain in sealed reports/data_coverage.md (lines 7, 8, 25) and tests/test_momentum.py (lines 19, 21, 26, 28, 30). These are intentionally preserved, not repaired.
