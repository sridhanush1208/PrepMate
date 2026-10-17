"""Loads the named Cypher queries in backend/queries/*.cypher.

Keeping every query in its own file makes it easy to list
"the Cypher queries the product depends on" in the README.
"""
from functools import lru_cache

from . import config


@lru_cache(maxsize=None)
def q(name: str) -> str:
    path = config.QUERIES_DIR / f"{name}.cypher"
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("//")
    ]
    return "\n".join(lines).strip()


def all_queries() -> dict[str, str]:
    return {p.stem: q(p.stem) for p in sorted(config.QUERIES_DIR.glob("*.cypher"))}
