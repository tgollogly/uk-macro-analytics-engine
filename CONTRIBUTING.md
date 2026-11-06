# Contributing

Thanks for your interest. This is a small portfolio project; contributions are welcome via pull request.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Checks before you push

```bash
ruff check src tests tools
python -m compileall -q src tests
python src/security_audit.py
pytest -q
```

## Style

- `ruff.toml` defines the linter; line length 100.
- Prefer small, focused commits and clear messages.

## Regenerating README bitmaps

```bash
pip install pillow
python3 tools/regen_readme_images.py
```
