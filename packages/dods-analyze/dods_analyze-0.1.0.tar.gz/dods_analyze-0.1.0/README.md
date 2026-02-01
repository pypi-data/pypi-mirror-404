# dods-analyze

Reusable analytics module for the DODS toolkit.

## Install

```bash
pip install dods-analyze
```

## Quick start

```python
from dods.analyze import DataAnalyzer
import pandas as pd

df = pd.read_csv("data.csv")
dfa = DataAnalyzer(df)

dfa.summary()

# Deep analysis (optional)
dfa.analyze_distributions()
dfa.analyze_missing()
dfa.analyze_outliers()
dfa.analyze_relations()
```

## API overview

```python
from dods.analyze import DataAnalyzer

# Class-level overview
DataAnalyzer.help()

# Instance-level (also works, equivalent)
dfa.help()
```

## Links

- Homepage: https://github.com/mahaeu/dods-analyze
