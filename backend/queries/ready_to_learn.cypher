// Topics whose prerequisites are all mastered, but which are not mastered yet.
// Sorted by how much the student's role cares, then by PageRank "foundational" score.
MATCH (s:Student)-[k:KNOWS]->(t:Topic)
WHERE k.mastery < $mastered
OPTIONAL MATCH (pre:Topic)-[:PREREQ_OF]->(t)
OPTIONAL MATCH (s)-[kp:KNOWS]->(pre)
WITH t, k, collect(kp.mastery) AS pre_mastery
WHERE all(m IN pre_mastery WHERE m >= $mastered)
RETURN t.id AS topic_id, t.name AS topic, k.mastery AS mastery,
       t.role_weight AS role_weight, t.foundational AS foundational
ORDER BY role_weight DESC, foundational DESC
LIMIT $limit
