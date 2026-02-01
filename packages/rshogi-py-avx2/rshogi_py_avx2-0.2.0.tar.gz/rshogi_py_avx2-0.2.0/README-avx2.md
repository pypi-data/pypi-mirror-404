# rshogi-py-avx2

AVX2 enabled build of the Python bindings for the `rshogi` Rust crate.

This package provides the same `rshogi` module as the standard package,
but it is compiled with `-C target-feature=+avx2` for x86_64 CPUs.

## Installation

```bash
python -m pip install rshogi-py-avx2
```

## Notes

- `rshogi-py` and `rshogi-py-avx2` are mutually exclusive; install only one.
- This build requires an AVX2-capable CPU on x86_64.
