#!/usr/bin/env python3
"""Write static-site/demo/macro-story.json from committed CPIH/PSNB snapshots."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.macro_story.compute import write_macro_story_json  # noqa: E402


def main() -> int:
    out = write_macro_story_json(ROOT)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
