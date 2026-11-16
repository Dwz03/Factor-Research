Configurations are JSON dictionaries consumed explicitly by research code:

```python
import json
from src.data.loader import PROJECT_ROOT
config = json.loads((PROJECT_ROOT / 'config/research.example.json').read_text())
# Opt-in network action: download_prices(**config['data'])
```

The example documents API parameters and reuses the existing notebook's symbols;
it is not a recommended research universe. Review coverage and universe selection
yourself before interpreting evaluations.
No configuration is automatically executed. Keep proxy settings in environment
variables or the ignored root `.env`, never in research configurations.

`universe.csv` freezes the 300-security sample constructed on 2026-11-12.
`universe.json` records the source snapshot checksum and deterministic selection
rule. The candidate CSV is retained locally under `data/universe/2026-11-12/`.
Sector quotas are proportional to the 503 candidates, rounded by largest
remainder (alphabetical sector ties); within sectors select the lowest SHA-256
hashes of `factor-research-universe-v1|source_ticker`. Price availability does not
affect selection. Current constituents and sectors introduce survivorship and
selection bias; this is not historical index membership.

`scripts/build_market_dataset.py` reproduces selection from that snapshot.
`--download` explicitly requests Yahoo data; it tests 10 securities, then batches
of up to 25 with 20-second pauses. Existing validated loader caches are reusable.
An existing merged output is protected against accidental reruns. The separate
`--recover-rejected` option permits one diagnostic pass on rejected batches only,
unless rate limiting was recorded. Diagnostics preserve raw responses and valid
columns separately, without weakening the loader's validation. No automatic
retry loop, ticker substitution, or forward filling is used.

See `reports/data_coverage.md` and the structured statistics under
`data/market/2026-11-12/` before using the matrix for research.
