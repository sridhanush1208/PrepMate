// Semantic memory: a fact, with provenance (which agent wrote it, from which message).
// MERGE on a normalised key so the same fact is updated, not duplicated.
MATCH (ag:Agent {name: $agent}), (m:Message {id: $message_id}), (about {id: $about_id})
MERGE (f:Fact {key: $key})
ON CREATE SET f.id = $id, f.ts = $now
SET f.text = $text, f.confidence = $confidence, f.updated = $now
MERGE (ag)-[:WROTE]->(f)
MERGE (f)-[:LEARNED_FROM]->(m)
MERGE (f)-[:ABOUT]->(about)
RETURN f.id AS id
