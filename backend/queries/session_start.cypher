// Episodic: a new session
MATCH (s:Student)
CREATE (s)-[:HAD]->(se:Session {id: $session_id, started_at: $now})
RETURN se.id AS id
