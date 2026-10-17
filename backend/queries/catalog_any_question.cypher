// Catalog: fallback when every question on the topic was already tried
MATCH (q:Question)-[:TESTS]->(t:Topic {id: $topic_id})
RETURN q.id AS id, q.text AS text, q.hint AS hint, q.points AS points,
       q.difficulty AS difficulty, t.id AS topic_id, t.name AS topic
ORDER BY q.difficulty
LIMIT 1
