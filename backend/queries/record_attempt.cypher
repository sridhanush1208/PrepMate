// Episodic + semantic: save the attempt and update mastery.
// First attempt: mastery = score. Later: new = 0.6 * old + 0.4 * score.
MATCH (:Student)-[k:KNOWS]->(t:Topic {id: $topic_id})
MATCH (se:Session {id: $session_id})
MATCH (ag:Agent {name: 'interviewer'})
MERGE (q:Question {id: $question.id})
ON CREATE SET q.text = $question.text, q.difficulty = $question.difficulty
MERGE (q)-[:TESTS]->(t)
CREATE (se)-[:INCLUDED]->(a:Attempt {id: $attempt_id, score: $score, feedback: $feedback, answer: $answer, ts: $now})-[:ON]->(q)
CREATE (ag)-[:WROTE]->(a)
WITH k, k.mastery AS old, k.attempts AS n
SET k.mastery = CASE WHEN n = 0 THEN $score ELSE (1.0 - $new_weight) * old + $new_weight * $score END,
    k.attempts = n + 1,
    k.last_practiced = $now
RETURN old AS old_mastery, k.mastery AS new_mastery, k.attempts AS attempts
