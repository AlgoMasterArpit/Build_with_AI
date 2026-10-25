"""Create the table if needed, load a hostel's rooms and print a new round link.

usage: uv run python scripts/seed.py seed/hostel_a.json

Existing rooms are left untouched, so re-running only adds a fresh link.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.store.seeding import seed_hostel
from app.store.table import Table


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    settings = get_settings()
    table = Table(settings)
    table.create_if_missing()
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    token = seed_hostel(table, data)
    print(f"{data['name']}: {len(data['rooms'])} rooms")
    print(f"round link: {settings.public_base_url.rstrip('/')}/r/{token}")


if __name__ == "__main__":
    main()
