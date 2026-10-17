// Episodic recall for "Welcome back": the latest previous session and its attempts
MATCH (:Student)-[:HAD]->(se:Session)
WHERE se.id <> $session_id
WITH se
ORDER BY se.started_at DESC
LIMIT 1
OPTIONAL MATCH (se)-[:INCLUDED]->(a:Attempt)-[:ON]->(:Question)-[:TESTS]->(t:Topic)
RETURN se.id AS session_id, se.started_at AS started_at, se.summary AS summary,
       collect(CASE WHEN a IS NULL THEN null ELSE {topic: t.name, topic_id: t.id, score: a.score} END) AS attempts
