// Topics practised but still weak
MATCH (:Student)-[k:KNOWS]->(t:Topic)
WHERE k.attempts > 0 AND k.mastery < $weak
RETURN t.id AS topic_id, t.name AS topic, k.mastery AS mastery, k.attempts AS attempts
ORDER BY k.mastery
LIMIT $limit
