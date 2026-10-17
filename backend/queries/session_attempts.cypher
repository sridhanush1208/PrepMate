// Attempts made in one session (used for the session summary)
MATCH (:Session {id: $session_id})-[:INCLUDED]->(a:Attempt)-[:ON]->(:Question)-[:TESTS]->(t:Topic)
RETURN t.name AS topic, a.score AS score
ORDER BY a.ts
