// Procedural memory: how an agent should behave for this student.
MATCH (writer:Agent {name: $agent}), (target:Agent {name: $applies_to}), (m:Message {id: $message_id})
MERGE (r:Rule {key: $key})
ON CREATE SET r.id = $id, r.ts = $now
SET r.text = $text, r.active = true, r.updated = $now
MERGE (writer)-[:WROTE]->(r)
MERGE (r)-[:APPLIES_TO]->(target)
MERGE (r)-[:LEARNED_FROM]->(m)
RETURN r.id AS id
