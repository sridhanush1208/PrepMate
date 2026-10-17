// Shared task board
MATCH (tk:Task {status: 'todo'})-[:ASSIGNED_TO]->(ag:Agent)
MATCH (tk)-[:PRACTICES]->(t:Topic)
RETURN tk.id AS id, tk.title AS title, tk.due AS due, ag.name AS agent, t.id AS topic_id, t.name AS topic
ORDER BY tk.due
