// Multi-hop: why is this topic hard? Walk back up to 3 PREREQ_OF steps
// and return prerequisites that are weak (or never tested).
MATCH p = (pre:Topic)-[:PREREQ_OF*1..3]->(:Topic {id: $topic_id})
MATCH (:Student)-[k:KNOWS]->(pre)
WHERE k.attempts = 0 OR k.mastery < $weak
WITH pre, k, min(length(p)) AS hops
RETURN pre.id AS topic_id, pre.name AS topic, k.mastery AS mastery,
       CASE WHEN k.attempts = 0 THEN 'untested' ELSE 'weak' END AS status, hops
ORDER BY status DESC, hops, mastery
LIMIT 5
