// Session state (pending mock-interview question, if any)
MATCH (se:Session {id: $session_id})
RETURN se.id AS id, se.started_at AS started_at,
       se.pending_question AS pending_question, se.pending_topic AS pending_topic
