// Catalog: pick a question for a topic that the student has not tried yet
MATCH (q:Question)-[:TESTS]->(t:Topic {id: $topic_id})
WHERE NOT q.id IN $exclude
RETURN q.id AS id, q.text AS text, q.hint AS hint, q.points AS points,
       q.difficulty AS difficulty, t.id AS topic_id, t.name AS topic
ORDER BY q.difficulty
LIMIT 1
