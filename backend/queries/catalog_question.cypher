// Catalog: one question by id
MATCH (q:Question {id: $id})-[:TESTS]->(t:Topic)
RETURN q.id AS id, q.text AS text, q.hint AS hint, q.points AS points,
       q.difficulty AS difficulty, t.id AS topic_id, t.name AS topic
