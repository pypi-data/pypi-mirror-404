# rshogi

Python bindings for the `rshogi` Rust crate.

## Development Install

```bash
python -m pip install maturin
maturin develop -m crates/rshogi-py/pyproject.toml
```

## AVX2 Build

`rshogi-py-avx2` is an AVX2-enabled build of the same Python module.

```bash
python -m pip install rshogi-py-avx2
```

## Quick Example

```python
import rshogi

board = rshogi.Board()
board.push("7g7f")
print(board.sfen())
```
