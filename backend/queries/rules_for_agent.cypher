// Procedural recall: active rules this agent must follow for this student
MATCH (r:Rule {active: true})-[:APPLIES_TO]->(:Agent {name: $agent})
RETURN r.id AS id, r.text AS text
ORDER BY r.ts DESC
LIMIT 10
