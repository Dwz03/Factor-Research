# Factor Library

Current research catalog. **Research status and evidence classification are separate:** Closed means the authorized research sequence is complete, not that a statistical gate passed or a tradable strategy exists.

| Factor ID | Name | Formula | Target | Investigated alpha orientation | Validation | Final held-out test | Research classification | Status |
|---|---|---|---|---|---|---|---|---|
| [001](../config/factor_library/001_momentum.json) | Momentum | P[t]/P[t-5] - 1 | Future 5D, entry lag 1 | Negative | Pass | Not Supported | Watchlist — Mixed Temporal Evidence | Closed |

## Momentum #001

Closed 2026-11-14 (Asia/Shanghai). [Final assessment](01_momentum_alpha_assessment_final.md) is the current interpretation; [pre-test assessment](01_momentum_alpha_assessment.md) remains historical evidence. [Final results](01_momentum_final_test_results.md) and [frozen protocol](01_momentum_final_test_protocol.md) are unchanged. The machine-readable record links every supporting report and recorded artifact and retains their hashes. [Closure receipt](archive/momentum_001/closure_integrity.json) records preservation verification. No rerun or revised hypothesis is authorized.

## Reusable catalog conventions

Create one `config/factor_library/<ID>_<name>.json` record per factor, with schema_version, string factor_id, factor_name, formula, target_horizon, target_formula, entry_lag, investigated_alpha_orientation, validation, final_held_out_test, research_classification, research_status, dated rationale and linked references/hashes. Keep protocol decisions verbatim; do not infer a Pass from completion or a favorable descriptive result.

Research classifications: **Alpha Candidate** (retain for further research, not confirmed Alpha), **Watchlist** (mixed or insufficient evidence), **Reject** (do not retain the current specification). Research status separately records Open or Closed. Record missing stages as Not Run, not as success. Preserve earlier assessments; date later interpretations and link them. Use the [Factor Assessment Template](FACTOR_ASSESSMENT_TEMPLATE.md). Add rows only for actual authorized studies; no Factor #002 has been created.
