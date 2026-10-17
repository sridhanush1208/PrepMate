// Memory panel: mastery for every practised topic
MATCH (:Student)-[k:KNOWS]->(t:Topic)
WHERE k.attempts > 0
RETURN t.id AS topic_id, t.name AS topic, t.area AS area, k.mastery AS mastery,
       k.attempts AS attempts, k.last_practiced AS last_practiced
ORDER BY k.mastery
