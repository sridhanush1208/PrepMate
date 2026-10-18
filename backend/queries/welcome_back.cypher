// Episodic recall for "Welcome back": how many earlier sessions there were, and the attempts
// from the latest earlier session that actually had practice (empty sessions are skipped).
MATCH (:Student)-[:HAD]->(se:Session)
WHERE se.id <> $session_id
WITH count(se) AS previous
OPTIONAL MATCH (:Student)-[:HAD]->(p:Session)-[:INCLUDED]->(:Attempt)
WHERE p.id <> $session_id
WITH previous, p
ORDER BY p.started_at DESC
LIMIT 1
OPTIONAL MATCH (p)-[:INCLUDED]->(a:Attempt)-[:ON]->(:Question)-[:TESTS]->(t:Topic)
RETURN previous, p.id AS session_id, p.started_at AS started_at, p.summary AS summary,
       collect(CASE WHEN a IS NULL THEN null ELSE {topic: t.name, topic_id: t.id, score: a.score} END) AS attempts
