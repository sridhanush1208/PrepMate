// Remember which question the Interviewer is waiting on
MATCH (se:Session {id: $session_id})
SET se.pending_question = $question_id, se.pending_topic = $topic_id
