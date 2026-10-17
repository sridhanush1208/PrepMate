// Procedural memory of ALL agents (so an agent doesn't save a rule that already exists for another agent)
MATCH (r:Rule {active: true})-[:APPLIES_TO]->(a:Agent)
RETURN r.text AS text, a.name AS applies_to
ORDER BY r.ts DESC
LIMIT 20
