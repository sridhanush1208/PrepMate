"""FalkorDB connection helpers.

One FalkorDB instance holds many graphs:
  - "catalog"          shared, read-only interview knowledge
  - "pm_<student_id>"  one private memory graph per student
"""
import re
import threading

from falkordb import FalkorDB

from . import config
from .queries import q

_db = None
_lock = threading.Lock()


def get_db() -> FalkorDB:
    global _db
    with _lock:
        if _db is None:
            _db = FalkorDB(
                host=config.FALKORDB_HOST,
                port=config.FALKORDB_PORT,
                username=config.FALKORDB_USERNAME,
                password=config.FALKORDB_PASSWORD,
            )
    return _db


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "student"


def graph_name(student_id: str) -> str:
    return f"{config.STUDENT_GRAPH_PREFIX}{student_id}"


def catalog():
    return get_db().select_graph(config.CATALOG_GRAPH)


def student_graph(student_id: str):
    return get_db().select_graph(graph_name(student_id))


def list_student_ids() -> list[str]:
    names = get_db().list_graphs()
    prefix = config.STUDENT_GRAPH_PREFIX
    return sorted(n[len(prefix):] for n in names if n.startswith(prefix))


def graph_exists(name: str) -> bool:
    return name in get_db().list_graphs()


def _decode(value):
    if isinstance(value, bytes):
        return value.decode()
    return value


def _column_names(result) -> list[str]:
    names = []
    for h in result.header:
        name = h[1] if isinstance(h, (list, tuple)) else h
        names.append(_decode(name))
    return names


def rows(graph, query_name: str, params: dict | None = None, read_only: bool = True) -> list[dict]:
    """Run a named query from backend/queries and return rows as dicts."""
    text = q(query_name)
    if read_only:
        result = graph.ro_query(text, params or {})
    else:
        result = graph.query(text, params or {})
    if not result.header:
        return []
    cols = _column_names(result)
    return [dict(zip(cols, row)) for row in result.result_set]


def write(graph, query_name: str, params: dict | None = None) -> list[dict]:
    return rows(graph, query_name, params, read_only=False)
