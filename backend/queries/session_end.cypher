// Episodic: close a session with a short summary
MATCH (se:Session {id: $session_id})
SET se.ended_at = $now, se.summary = $summary
