# rshogi

Python bindings for the `rshogi-core` crate.

## Development Install

```bash
python -m pip install maturin
maturin develop -m crates/rshogi/pyproject.toml
```

## Quick Example

```python
import rshogi

board = rshogi.Board()
board.push("7g7f")
print(board.sfen())
```
