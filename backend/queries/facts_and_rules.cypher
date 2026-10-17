// Memory panel: facts and rules with where they came from
MATCH (x)
WHERE x:Fact OR x:Rule
OPTIONAL MATCH (x)-[:LEARNED_FROM]->(m:Message)
OPTIONAL MATCH (w:Agent)-[:WROTE]->(x)
OPTIONAL MATCH (x)-[:APPLIES_TO]->(ap:Agent)
OPTIONAL MATCH (x)-[:ABOUT]->(ab)
RETURN x.id AS id, labels(x)[0] AS kind, x.text AS text, x.updated AS ts,
       m.text AS source_text, w.name AS written_by, ap.name AS applies_to, ab.name AS about
ORDER BY ts DESC
