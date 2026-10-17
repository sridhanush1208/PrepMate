// The pending question was answered
MATCH (se:Session {id: $session_id})
SET se.pending_question = null, se.pending_topic = null
