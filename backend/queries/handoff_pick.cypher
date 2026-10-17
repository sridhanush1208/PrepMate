// Coordination: the receiving agent picked up the handoff
MATCH (h:Handoff {id: $id})
SET h.status = 'picked', h.picked_at = $now
