"""
Decides whether a trading-desk branch may be auto-merged into master.

The desk routine can only push to claude/* branches. desk-merge.yml merges a
branch only when every changed path is desk output; anything else (code,
workflows, strategy specs, robot state) waits for Rayyan's review.

Usage: git diff --name-only A...B | python -m routines_pkg.desk_merge_guard
Exit 0 = mergeable, 1 = blocked (blocked paths printed).
"""
from __future__ import annotations

import re
import sys

_ALLOWED = re.compile(
    r"^(journal/[^/]+\.md"
    r"|memory/(desk-notes\.md|desk-alert\.txt)"
    r"|research/[\w./-]+\.md"
    r"|backtests/[\w./-]+"
    r"|\.HALT)$"
)


def blocked_paths(paths: list[str]) -> list[str]:
    return [p for p in paths if ".." in p.split("/") or not _ALLOWED.match(p)]


def main() -> int:
    paths = [line.strip() for line in sys.stdin if line.strip()]
    blocked = blocked_paths(paths)
    for p in blocked:
        print(p)
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
