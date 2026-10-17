// Conversation history: last N messages in this session
MATCH (:Session {id: $session_id})-[:HAS_MSG]->(m:Message)
RETURN m.id AS id, m.role AS role, m.agent AS agent, m.text AS text, m.ts AS ts
ORDER BY m.ts DESC
LIMIT $limit
