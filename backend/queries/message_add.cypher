// Conversation history: add a message and chain it to the previous one with NEXT.
// seq gives a strict order even when two messages share the same millisecond.
MATCH (se:Session {id: $session_id})
WITH se, se.last_msg_id AS prev, coalesce(se.msg_count, 0) + 1 AS seq
CREATE (se)-[:HAS_MSG]->(m:Message {id: $id, seq: seq, role: $role, agent: $agent, text: $text, ts: $now})
SET se.last_msg_id = $id, se.msg_count = seq
WITH prev, m
OPTIONAL MATCH (p:Message {id: prev})
WITH p, m
WHERE p IS NOT NULL
CREATE (p)-[:NEXT]->(m)
