# rshogi

Python bindings for the `rshogi-core` crate.

## Development Install

```bash
python -m pip install maturin
maturin develop -m crates/rshogi/pyproject.toml
```

## AVX2 Build

`rshogi-avx2` is an AVX2-enabled build of the same Python module.

```bash
python -m pip install rshogi-avx2
```

## Quick Example

```python
import rshogi

board = rshogi.Board()
board.push("7g7f")
print(board.sfen())
```
