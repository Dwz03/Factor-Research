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
