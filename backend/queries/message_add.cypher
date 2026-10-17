// Conversation history: add a message and chain it to the previous one with NEXT
MATCH (se:Session {id: $session_id})
WITH se, se.last_msg_id AS prev
CREATE (se)-[:HAS_MSG]->(m:Message {id: $id, role: $role, agent: $agent, text: $text, ts: $now})
SET se.last_msg_id = $id
WITH prev, m
OPTIONAL MATCH (p:Message {id: prev})
WITH p, m
WHERE p IS NOT NULL
CREATE (p)-[:NEXT]->(m)
