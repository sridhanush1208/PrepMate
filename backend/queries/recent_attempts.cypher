// Episodic recall: last attempts on a topic
MATCH (a:Attempt)-[:ON]->(q:Question)-[:TESTS]->(:Topic {id: $topic_id})
RETURN a.id AS id, q.text AS question, a.score AS score, a.feedback AS feedback, a.ts AS ts
ORDER BY a.ts DESC
LIMIT 3
