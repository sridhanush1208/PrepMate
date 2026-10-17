"""Load catalog/*.yaml into the shared "catalog" graph and compute PageRank.

Run from backend/:  uv run python -m scripts.seed_catalog
"""
import yaml

from app import config
from app.db import catalog, rows, write


def load_yaml(name: str) -> dict:
    with open(config.CATALOG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    topics = load_yaml("topics.yaml")["topics"]
    questions = load_yaml("questions.yaml")["questions"]
    roles = load_yaml("roles.yaml")["roles"]

    topic_ids = {t["id"] for t in topics}
    for t in topics:
        for p in t["prereqs"]:
            assert p in topic_ids, f"unknown prereq {p} in {t['id']}"
    for qu in questions:
        assert qu["topic"] in topic_ids, f"unknown topic {qu['topic']} in {qu['id']}"

    g = catalog()
    try:
        g.delete()  # rebuild from scratch so YAML edits always apply
    except Exception:
        pass
    g = catalog()
    for stmt in ("CREATE INDEX FOR (t:Topic) ON (t.id)", "CREATE INDEX FOR (q:Question) ON (q.id)"):
        g.query(stmt)

    write(g, "catalog_load_topics", {"topics": [{"id": t["id"], "name": t["name"], "area": t["area"]} for t in topics]})
    prereqs = [{"src": p, "dst": t["id"]} for t in topics for p in t["prereqs"]]
    write(g, "catalog_load_prereqs", {"prereqs": prereqs})
    write(g, "catalog_load_questions", {"questions": questions})
    focus = [
        {"role_id": r["id"], "role_name": r["name"], "topic": topic, "weight": weight}
        for r in roles for topic, weight in r["focus"].items()
    ]
    write(g, "catalog_load_roles", {"focus": focus})

    scores = rows(g, "pagerank_foundational")
    write(g, "catalog_set_foundational", {"scores": scores})
    top = sorted(scores, key=lambda s: s["score"], reverse=True)[:5]

    print(f"catalog: {len(topics)} topics, {len(prereqs)} prerequisites, "
          f"{len(questions)} questions, {len(roles)} roles")
    print("most foundational (PageRank):", ", ".join(f"{s['topic_id']}={s['score']:.3f}" for s in top))


if __name__ == "__main__":
    main()
