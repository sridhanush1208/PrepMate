// Coordination: one agent hands work to another
MATCH (f:Agent {name: $from_agent}), (t:Agent {name: $to_agent}), (se:Session {id: $session_id})
CREATE (h:Handoff {id: $id, reason: $reason, ts: $now, status: 'open'})
CREATE (h)-[:FROM]->(f), (h)-[:TO]->(t), (h)-[:IN]->(se)
WITH h
OPTIONAL MATCH (tp:Topic {id: $topic_id})
WITH h, tp
WHERE tp IS NOT NULL
CREATE (h)-[:ABOUT]->(tp)
