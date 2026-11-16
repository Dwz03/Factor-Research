# Momentum #001 staged whitespace exception

Reviewed on 2026-11-16 (Asia/Shanghai) for the byte-preserving Momentum #001 archive. This note is new and is not part of any frozen research seal.

`git diff --cached --check` exited 2 with **8,137** diagnostics. Every diagnostic was parsed and checked against the corresponding staged Git blob:

- **8,129** are CRLF line endings already present in the preserved working-tree bytes. They were flagged because the default Git whitespace setting treats carriage returns at line endings as whitespace.
- **Eight** are literal trailing spaces: `reports/data_coverage.md` lines **7, 8, 25** and `tests/test_momentum.py` lines **19, 21, 26, 28, 30**. These were documented in the previous archival audit. The report is preserved research evidence; the test file is retained byte-for-byte with its historical staged version.
- **Zero** diagnostics were unknown, related to conflict markers, missing files, or non-whitespace content.

The check was run on the full staged diff, not a sample. All staged Git blobs matched their working-tree files exactly. `core.autocrlf=false` was used for staging, and no sealed file was normalized or edited. The exception applies only to these identified historical formatting diagnostics; it does not waive future byte-integrity or sensitive-file checks. If the staged set changes, rerun the full classification.
