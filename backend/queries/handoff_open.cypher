// Coordination: newest open handoff waiting for this agent
MATCH (h:Handoff {status: 'open'})-[:TO]->(:Agent {name: $agent})
MATCH (h)-[:FROM]->(f:Agent)
OPTIONAL MATCH (h)-[:ABOUT]->(t:Topic)
RETURN h.id AS id, h.reason AS reason, f.name AS from_agent, t.id AS topic_id, t.name AS topic
ORDER BY h.ts DESC
LIMIT 1
