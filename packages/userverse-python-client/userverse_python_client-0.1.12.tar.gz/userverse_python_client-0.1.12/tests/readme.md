# Testing guide

Run the test suite from the project root:

```bash
pytest
```

Notes:
- Tests rely on lightweight stubs defined in `tests/conftest.py` to avoid installing the external shared models.
- If you prefer to use the real shared models, install project dependencies first and then run `pytest`.
