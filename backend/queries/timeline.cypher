// Memory panel: sessions with their attempts (episodic timeline)
MATCH (:Student)-[:HAD]->(se:Session)
OPTIONAL MATCH (se)-[:INCLUDED]->(a:Attempt)-[:ON]->(:Question)-[:TESTS]->(t:Topic)
WITH se, a, t
ORDER BY a.ts
WITH se, collect(CASE WHEN a IS NULL THEN null ELSE {topic: t.name, score: a.score, ts: a.ts} END) AS attempts
OPTIONAL MATCH (h:Handoff)-[:IN]->(se)
RETURN se.id AS session_id, se.started_at AS started_at, se.summary AS summary,
       attempts, count(h) AS handoffs
ORDER BY started_at DESC
