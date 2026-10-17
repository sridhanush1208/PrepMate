// What the student knows about one topic
MATCH (:Student)-[k:KNOWS]->(t:Topic {id: $topic_id})
RETURN t.id AS topic_id, t.name AS topic, k.mastery AS mastery,
       k.attempts AS attempts, k.last_practiced AS last_practiced
