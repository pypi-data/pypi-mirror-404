# rshogi (migration package)

This PyPI distribution name is kept for backwards compatibility.

## What you should install

Prefer:

```bash
python -m pip install rshogi-py
```

This package exists so that existing instructions like:

```bash
python -m pip install rshogi
```

keep working by installing `rshogi-py` under the hood.

## Import name

The Python import name remains:

```python
import rshogi
```

It is provided by `rshogi-py`, not by this shim package.

